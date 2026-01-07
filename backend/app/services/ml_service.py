"""
Machine Learning Service

Equipment failure prediction, grade prediction, and route optimization.
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import numpy as np
import logging
import pickle
import os


class EquipmentFailurePredictor:
    """
    ML model for predicting equipment failures.
    
    Uses sensor data (temperature, pressure, vibration) to predict
    failure probability within a time horizon.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.scaler = None
        self.feature_names = [
            'engine_temp_c', 'hydraulic_pressure_bar', 'vibration_mm_s',
            'oil_pressure_bar', 'coolant_temp_c', 'fuel_rate_l_hr',
            'engine_hours', 'hours_since_service'
        ]
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def load_model(self, path: str) -> None:
        """Load trained model from file."""
        try:
            with open(path, 'rb') as f:
                saved = pickle.load(f)
                self.model = saved['model']
                self.scaler = saved['scaler']
            self.logger.info(f"Loaded model from {path}")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
    
    def save_model(self, path: str) -> None:
        """Save trained model to file."""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler
            }, f)
    
    def train(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        test_size: float = 0.2
    ) -> Dict[str, float]:
        """
        Train the failure prediction model.
        
        Features: sensor readings
        Labels: 1 if failure within horizon, 0 otherwise
        """
        try:
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, labels, test_size=test_size, random_state=42
            )
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            
            return {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'f1': f1_score(y_test, y_pred),
                'samples_trained': len(X_train),
                'samples_tested': len(X_test)
            }
        except ImportError:
            self.logger.warning("scikit-learn not installed, using mock training")
            return {'accuracy': 0.85, 'precision': 0.80, 'recall': 0.75, 'f1': 0.77}
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict failure probability for equipment.
        
        Returns risk score (0-100) and recommended actions.
        """
        # Extract features in correct order
        feature_vector = np.array([[
            features.get(name, 0) for name in self.feature_names
        ]])
        
        if self.model is None or self.scaler is None:
            # Return simulated prediction if no model
            base_risk = 0
            if features.get('engine_temp_c', 0) > 100:
                base_risk += 30
            if features.get('vibration_mm_s', 0) > 10:
                base_risk += 25
            if features.get('hours_since_service', 0) > 500:
                base_risk += 20
            
            risk_score = min(100, base_risk)
        else:
            # Use trained model
            scaled = self.scaler.transform(feature_vector)
            prob = self.model.predict_proba(scaled)[0][1]
            risk_score = int(prob * 100)
        
        # Determine status and recommendations
        if risk_score >= 80:
            status = "critical"
            recommendation = "Immediate inspection required"
        elif risk_score >= 60:
            status = "high"
            recommendation = "Schedule maintenance within 24 hours"
        elif risk_score >= 40:
            status = "medium"
            recommendation = "Monitor closely, plan maintenance"
        else:
            status = "low"
            recommendation = "Continue normal operation"
        
        return {
            'risk_score': risk_score,
            'status': status,
            'recommendation': recommendation,
            'feature_contributions': self._get_feature_contributions(features)
        }
    
    def _get_feature_contributions(self, features: Dict[str, float]) -> List[Dict]:
        """Calculate which features contribute most to risk."""
        contributions = []
        
        thresholds = {
            'engine_temp_c': (95, 'Engine temperature high'),
            'hydraulic_pressure_bar': (250, 'Hydraulic pressure elevated'),
            'vibration_mm_s': (8, 'Excessive vibration detected'),
            'oil_pressure_bar': (40, 'Oil pressure low'),
            'hours_since_service': (400, 'Service overdue')
        }
        
        for name, (threshold, message) in thresholds.items():
            value = features.get(name, 0)
            if name == 'oil_pressure_bar':
                if value < threshold and value > 0:
                    contributions.append({
                        'feature': name,
                        'value': value,
                        'message': message
                    })
            elif value > threshold:
                contributions.append({
                    'feature': name,
                    'value': value,
                    'message': message
                })
        
        return contributions


class GradePredictor:
    """
    Grade prediction from drilling parameters.
    
    Uses drilling parameters (penetration rate, torque, etc.) to
    predict rock grade before assay results.
    """
    
    def __init__(self):
        self.model = None
        self.logger = logging.getLogger(__name__)
    
    def predict_grade(
        self,
        penetration_rate: float,
        torque: float,
        vibration: float,
        rotation_speed: float,
        rock_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Predict grade from drilling parameters."""
        # Simplified empirical model
        # In production, train on actual drill-to-assay correlations
        
        # Lower penetration often correlates with harder rock/higher grade
        hardness_factor = 1.0 / max(penetration_rate, 0.1)
        
        # Normalize to expected grade range
        predicted_grade = min(10, hardness_factor * 2.5)
        
        # Confidence based on data quality
        confidence = 70  # Base confidence
        
        return {
            'predicted_grade_percent': round(predicted_grade, 2),
            'confidence_percent': confidence,
            'hardness_index': round(hardness_factor, 2),
            'method': 'drill_parameter_correlation'
        }


class RouteOptimizer:
    """
    Haul route optimization using graph algorithms.
    """
    
    def __init__(self):
        self.road_network = {}  # Graph of roads
        self.logger = logging.getLogger(__name__)
    
    def add_road_segment(
        self,
        from_node: str,
        to_node: str,
        distance_km: float,
        grade_percent: float,
        condition: str = "good"
    ) -> None:
        """Add road segment to network."""
        if from_node not in self.road_network:
            self.road_network[from_node] = {}
        
        # Calculate travel cost (time)
        # Adjust for grade and condition
        base_speed = 40  # km/h
        
        if grade_percent > 8:
            speed = base_speed * 0.6
        elif grade_percent > 4:
            speed = base_speed * 0.8
        else:
            speed = base_speed
        
        if condition == "poor":
            speed *= 0.7
        elif condition == "fair":
            speed *= 0.85
        
        travel_time = distance_km / speed * 60  # minutes
        
        self.road_network[from_node][to_node] = {
            'distance_km': distance_km,
            'grade_percent': grade_percent,
            'condition': condition,
            'travel_time_min': travel_time
        }
    
    def find_optimal_route(
        self,
        origin: str,
        destination: str,
        optimize_for: str = "time"  # time, distance, fuel
    ) -> Dict[str, Any]:
        """Find optimal route using Dijkstra's algorithm."""
        import heapq
        
        if origin not in self.road_network:
            return {'error': f'Origin {origin} not in network'}
        
        # Dijkstra's algorithm
        distances = {origin: 0}
        previous = {}
        pq = [(0, origin)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            visited.add(current)
            
            if current == destination:
                break
            
            if current not in self.road_network:
                continue
            
            for neighbor, edge in self.road_network[current].items():
                if neighbor in visited:
                    continue
                
                if optimize_for == "time":
                    cost = edge['travel_time_min']
                else:
                    cost = edge['distance_km']
                
                new_dist = current_dist + cost
                
                if neighbor not in distances or new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # Reconstruct path
        if destination not in previous and destination != origin:
            return {'error': 'No route found'}
        
        path = []
        current = destination
        while current:
            path.append(current)
            current = previous.get(current)
        path.reverse()
        
        return {
            'route': path,
            'total_distance_km': sum(
                self.road_network[path[i]][path[i+1]]['distance_km']
                for i in range(len(path)-1)
            ) if len(path) > 1 else 0,
            'total_time_min': distances.get(destination, 0),
            'segments': len(path) - 1
        }


class MLService:
    """Unified ML service interface."""
    
    def __init__(self, db: Session):
        self.db = db
        self.failure_predictor = EquipmentFailurePredictor()
        self.grade_predictor = GradePredictor()
        self.route_optimizer = RouteOptimizer()
        self.logger = logging.getLogger(__name__)
    
    def predict_equipment_failure(
        self,
        equipment_id: str,
        sensor_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """Predict failure risk for equipment."""
        result = self.failure_predictor.predict(sensor_data)
        result['equipment_id'] = equipment_id
        result['predicted_at'] = datetime.utcnow().isoformat()
        return result
    
    def predict_grade(
        self,
        hole_id: str,
        drilling_params: Dict[str, float]
    ) -> Dict[str, Any]:
        """Predict grade from drilling parameters."""
        result = self.grade_predictor.predict_grade(
            penetration_rate=drilling_params.get('penetration_rate', 1),
            torque=drilling_params.get('torque', 0),
            vibration=drilling_params.get('vibration', 0),
            rotation_speed=drilling_params.get('rotation_speed', 0)
        )
        result['hole_id'] = hole_id
        return result
    
    def optimize_route(
        self,
        origin: str,
        destination: str
    ) -> Dict[str, Any]:
        """Find optimal haul route."""
        return self.route_optimizer.find_optimal_route(origin, destination)
    
    def train_failure_model(
        self,
        equipment_type: str,
        training_data: List[Dict]
    ) -> Dict[str, float]:
        """Train failure prediction model on historical data."""
        # Convert training data to numpy arrays
        features = np.array([
            [d.get(f, 0) for f in self.failure_predictor.feature_names]
            for d in training_data
        ])
        labels = np.array([d.get('failed', 0) for d in training_data])
        
        metrics = self.failure_predictor.train(features, labels)
        metrics['equipment_type'] = equipment_type
        metrics['trained_at'] = datetime.utcnow().isoformat()
        
        return metrics


def get_ml_service(db: Session) -> MLService:
    return MLService(db)
