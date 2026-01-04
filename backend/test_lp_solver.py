"""
Quick test for LP Material Allocator
"""
import sys
sys.path.insert(0, '.')

from scipy.optimize import linprog
import numpy as np

def test_scipy_lp():
    """Test basic scipy LP solver."""
    print("Testing scipy LP solver...")
    
    # Simple problem: minimize 2x + 3y
    # Subject to: x + y >= 1, x >= 0, y >= 0
    
    c = [2, 3]  # Minimize 2x + 3y
    A_ub = [[-1, -1]]  # -x - y <= -1 (equivalent to x + y >= 1)
    b_ub = [-1]
    bounds = [(0, None), (0, None)]
    
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    
    print(f"Success: {result.success}")
    print(f"Solution: x={result.x[0]:.2f}, y={result.x[1]:.2f}")
    print(f"Optimal value: {result.fun:.2f}")
    
    assert result.success, "LP should succeed"
    assert abs(result.x[0] - 1.0) < 0.01, "x should be 1"
    assert abs(result.x[1] - 0.0) < 0.01, "y should be 0"
    assert abs(result.fun - 2.0) < 0.01, "Optimal value should be 2"
    
    print("✅ Basic LP test PASSED")
    return True


def test_material_routing():
    """Test a material routing style LP."""
    print("\nTesting material routing LP formulation...")
    
    # 2 parcels, 2 arcs each can go to
    # Parcel 1: 100t, can go to Arc A (cost 5) or Arc B (cost 10)
    # Parcel 2: 50t, can go to Arc A (cost 8) or Arc B (cost 6)
    # Arc A capacity: 120t
    # Arc B capacity: 100t
    
    # Variables: x1A, x1B, x2A, x2B (tonnes of parcel i to arc j)
    # Minimize: 5*x1A + 10*x1B + 8*x2A + 6*x2B
    
    c = [5, 10, 8, 6]
    
    # Constraints:
    # x1A + x1B = 100 (all of parcel 1 allocated)
    # x2A + x2B = 50 (all of parcel 2 allocated)
    # x1A + x2A <= 120 (Arc A capacity)
    # x1B + x2B <= 100 (Arc B capacity)
    
    A_eq = [
        [1, 1, 0, 0],  # Parcel 1 fully allocated
        [0, 0, 1, 1],  # Parcel 2 fully allocated
    ]
    b_eq = [100, 50]
    
    A_ub = [
        [1, 0, 1, 0],  # Arc A capacity
        [0, 1, 0, 1],  # Arc B capacity
    ]
    b_ub = [120, 100]
    
    bounds = [(0, 100), (0, 100), (0, 50), (0, 50)]
    
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    
    print(f"Success: {result.success}")
    print(f"Solution: x1A={result.x[0]:.1f}t, x1B={result.x[1]:.1f}t, x2A={result.x[2]:.1f}t, x2B={result.x[3]:.1f}t")
    print(f"Total cost: ${result.fun:.0f}")
    
    # Expected: Send all 100t of parcel 1 to Arc A (cheaper), send all 50t of parcel 2 to Arc B (cheaper)
    # Total cost = 100*5 + 50*6 = 500 + 300 = 800
    
    assert result.success, "LP should succeed"
    assert abs(result.x[0] - 100) < 1, "x1A should be 100"
    assert abs(result.x[1] - 0) < 1, "x1B should be 0"
    assert abs(result.x[2] - 0) < 1, "x2A should be 0"
    assert abs(result.x[3] - 50) < 1, "x2B should be 50"
    assert abs(result.fun - 800) < 1, "Total cost should be 800"
    
    print("✅ Material routing LP test PASSED")
    return True


if __name__ == "__main__":
    try:
        test_scipy_lp()
        test_material_routing()
        print("\n🎉 All LP solver tests PASSED!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
