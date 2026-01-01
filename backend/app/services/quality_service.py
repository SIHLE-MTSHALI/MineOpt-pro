from typing import Dict, List, Optional
from ..domain import models_resource

class QualityService:
    @staticmethod
    def validate_quality_vector(quality_vector: Dict[str, float], fields: List[models_resource.QualityField]) -> List[str]:
        """
        Validates that a quality vector matches the site's defined fields.
        Returns a list of warnings/errors.
        """
        errors = []
        for field in fields:
            if field.name not in quality_vector:
                if field.missing_data_policy == "Error":
                    errors.append(f"Missing required quality field: {field.name}")
                # else if "Warning" or "Ignore", handled implicitly
        return errors

    @staticmethod
    def convert_basis(
        value: float, 
        start_basis: str, 
        target_basis: str, 
        moisture_arb: float = 0.0, 
        moisture_adb: float = 0.0
    ) -> float:
        """
        Converts a value between bases (ARB, ADB, DB, DAF).
        Supported: ARB -> ADB, ADB -> ARB (simplified).
        Requires Total Moisture (TM) for ARB and Inherent Moisture (IM) for ADB.
        
        Formulae (Simplified ISO):
        ADB = ARB * ((100 - IM) / (100 - TM))
        """
        if start_basis == target_basis:
            return value
            
        # Example Implementation for CV (Calorific Value)
        # Assuming value decreases with moisture
        
        # ARB to ADB
        # Factor = (100 - IM) / (100 - TM)
        # usually TM > IM, so Factor > 1. ADB value > ARB value
        
        factor = 1.0
        if start_basis == "ARB" and target_basis == "ADB":
            # Avoid division by zero
            if 100 - moisture_arb == 0: return 0
            factor = (100 - moisture_adb) / (100 - moisture_arb)
            
        elif start_basis == "ADB" and target_basis == "ARB":
             if 100 - moisture_adb == 0: return 0
             factor = (100 - moisture_arb) / (100 - moisture_adb)
             
        return round(value * factor, 4)
