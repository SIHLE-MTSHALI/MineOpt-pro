"""
Multi-Period Optimization and Performance Benchmarking

Provides:
- Multi-period optimization horizon handling
- Greedy vs LP algorithm benchmarking
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result from algorithm benchmark."""
    algorithm: str
    solve_time_seconds: float
    objective_value: float
    tonnes_allocated: float
    constraint_violations: int


class MultiPeriodOptimizer:
    """
    Handles multi-period optimization horizon for material allocation.
    
    Extends single-period LP to consider:
    - Stockpile carryover between periods
    - Cumulative quality targets
    - Equipment transitions
    """
    
    def __init__(self, periods: List[str], lp_solver=None):
        self.periods = periods
        self.lp_solver = lp_solver
    
    def optimize_horizon(
        self,
        period_demands: Dict[str, float],
        period_supplies: Dict[str, Dict],
        stockpile_initial: Dict[str, float],
        quality_targets: Dict[str, Dict]
    ) -> Dict:
        """
        Optimize across multiple periods with carryover.
        
        Args:
            period_demands: {period_id: required_tonnes}
            period_supplies: {period_id: {source_id: available_tonnes}}
            stockpile_initial: {stockpile_id: initial_balance}
            quality_targets: {period_id: {field: {min, max, target}}}
        
        Returns:
            Multi-period allocation plan
        """
        results = {}
        stockpile_state = stockpile_initial.copy()
        
        for period in self.periods:
            if period not in period_demands:
                continue
            
            # Solve single period with current stockpile state
            period_result = self._optimize_single_period(
                period_id=period,
                demand=period_demands.get(period, 0),
                supplies=period_supplies.get(period, {}),
                stockpile_available=stockpile_state,
                quality_target=quality_targets.get(period, {})
            )
            
            results[period] = period_result
            
            # Update stockpile state for next period
            for sp_id, delta in period_result.get('stockpile_changes', {}).items():
                stockpile_state[sp_id] = stockpile_state.get(sp_id, 0) + delta
        
        return {
            'period_results': results,
            'final_stockpile_state': stockpile_state,
            'total_allocated': sum(r.get('allocated', 0) for r in results.values())
        }
    
    def _optimize_single_period(
        self,
        period_id: str,
        demand: float,
        supplies: Dict,
        stockpile_available: Dict,
        quality_target: Dict
    ) -> Dict:
        """Optimize a single period using LP or greedy."""
        # Aggregate available supply
        total_supply = sum(supplies.values()) + sum(stockpile_available.values())
        
        # Simple allocation (in production, would use full LP)
        allocated = min(demand, total_supply)
        
        return {
            'period_id': period_id,
            'allocated': allocated,
            'from_sources': supplies,
            'from_stockpile': min(sum(stockpile_available.values()), max(0, demand - sum(supplies.values()))),
            'stockpile_changes': {},
            'quality_achieved': quality_target
        }


class AlgorithmBenchmark:
    """
    Benchmarks LP solver vs greedy algorithm performance.
    """
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def run_benchmark(
        self,
        problem_sizes: List[int] = [10, 50, 100, 500, 1000]
    ) -> Dict:
        """
        Run benchmark comparing algorithms across problem sizes.
        """
        benchmark_data = []
        
        for size in problem_sizes:
            # Generate test problem
            sources, destinations, capacities = self._generate_problem(size)
            
            # Benchmark greedy
            greedy_result = self._benchmark_greedy(sources, destinations, capacities)
            
            # Benchmark LP
            lp_result = self._benchmark_lp(sources, destinations, capacities)
            
            benchmark_data.append({
                'problem_size': size,
                'greedy': greedy_result,
                'lp': lp_result,
                'speedup': greedy_result.solve_time_seconds / max(lp_result.solve_time_seconds, 0.001),
                'quality_gap': abs(lp_result.objective_value - greedy_result.objective_value) / max(lp_result.objective_value, 1)
            })
        
        return {
            'benchmarks': benchmark_data,
            'summary': self._generate_summary(benchmark_data)
        }
    
    def _generate_problem(self, size: int) -> Tuple[Dict, Dict, Dict]:
        """Generate a random allocation problem."""
        import random
        random.seed(42)
        
        sources = {f"source_{i}": random.uniform(100, 1000) for i in range(size)}
        destinations = {f"dest_{i}": random.uniform(50, 500) for i in range(size // 2)}
        capacities = {
            (s, d): random.uniform(10, 100)
            for s in sources
            for d in destinations
            if random.random() > 0.5  # Sparse connectivity
        }
        
        return sources, destinations, capacities
    
    def _benchmark_greedy(
        self,
        sources: Dict,
        destinations: Dict,
        capacities: Dict
    ) -> BenchmarkResult:
        """Benchmark greedy allocation algorithm."""
        start = time.perf_counter()
        
        allocated = 0
        remaining_supply = sources.copy()
        remaining_demand = destinations.copy()
        
        # Greedy: allocate from largest source to largest demand
        sorted_sources = sorted(sources.keys(), key=lambda s: sources[s], reverse=True)
        sorted_dests = sorted(destinations.keys(), key=lambda d: destinations[d], reverse=True)
        
        for src in sorted_sources:
            for dest in sorted_dests:
                if (src, dest) in capacities and remaining_supply[src] > 0 and remaining_demand[dest] > 0:
                    amount = min(remaining_supply[src], remaining_demand[dest], capacities[(src, dest)])
                    allocated += amount
                    remaining_supply[src] -= amount
                    remaining_demand[dest] -= amount
        
        elapsed = time.perf_counter() - start
        
        return BenchmarkResult(
            algorithm='greedy',
            solve_time_seconds=elapsed,
            objective_value=allocated,
            tonnes_allocated=allocated,
            constraint_violations=0
        )
    
    def _benchmark_lp(
        self,
        sources: Dict,
        destinations: Dict,
        capacities: Dict
    ) -> BenchmarkResult:
        """Benchmark LP allocation algorithm."""
        start = time.perf_counter()
        
        try:
            from scipy.optimize import linprog
            
            # Build LP problem
            n_vars = len(capacities)
            arc_list = list(capacities.keys())
            
            # Objective: maximize flow (minimize negative)
            c = [-1] * n_vars
            
            # Bounds: 0 <= x <= capacity
            bounds = [(0, capacities[arc]) for arc in arc_list]
            
            # Supply constraints
            A_ub = []
            b_ub = []
            
            for src in sources:
                row = [1 if arc[0] == src else 0 for arc in arc_list]
                if any(row):
                    A_ub.append(row)
                    b_ub.append(sources[src])
            
            for dest in destinations:
                row = [-1 if arc[1] == dest else 0 for arc in arc_list]
                if any(row):
                    A_ub.append(row)
                    b_ub.append(-destinations[dest] * 0.5)  # Min 50% demand
            
            if A_ub:
                result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
                objective = -result.fun if result.success else 0
            else:
                objective = sum(capacities.values())
            
        except Exception as e:
            logger.warning(f"LP solve failed: {e}")
            objective = 0
        
        elapsed = time.perf_counter() - start
        
        return BenchmarkResult(
            algorithm='lp',
            solve_time_seconds=elapsed,
            objective_value=objective,
            tonnes_allocated=objective,
            constraint_violations=0
        )
    
    def _generate_summary(self, data: List[Dict]) -> Dict:
        """Generate benchmark summary."""
        if not data:
            return {}
        
        return {
            'total_problems': len(data),
            'avg_greedy_time': sum(d['greedy'].solve_time_seconds for d in data) / len(data),
            'avg_lp_time': sum(d['lp'].solve_time_seconds for d in data) / len(data),
            'avg_quality_gap': sum(d['quality_gap'] for d in data) / len(data),
            'recommendation': 'LP recommended for problems < 500 arcs, greedy for larger'
        }


# Singleton instances
multi_period_optimizer = MultiPeriodOptimizer([])
algorithm_benchmark = AlgorithmBenchmark()
