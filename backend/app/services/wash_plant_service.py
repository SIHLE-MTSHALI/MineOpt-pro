from typing import Dict, Tuple, Optional
from ..domain import models_flow

class WashPlantService:
    @staticmethod
    def calculate_yield_and_quality(
        feed_quality: Dict[str, float],
        target_ash: float,
        efficiency_factor: float = 0.95
    ) -> Tuple[float, Dict[str, float]]:
        """
        Simulates a wash run.
        Returns (Yield_Fraction, Product_Quality_Vector).
        
        Logic (Simplified Dense Medium Cyclone Model):
        - Theoretical Yield is inversely proportional to Feed Ash vs Target Ash.
        - If Feed Ash <= Target Ash, Yield = 100% (Bypass).
        - If Feed Ash is high, Yield drops.
        """
        
        feed_ash = feed_quality.get("Ash_ADB", 25.0) # Default if missing
        feed_cv = feed_quality.get("CV_ARB", 20.0)
        
        # 1. Bypass condition
        if feed_ash <= target_ash:
            return 1.0, feed_quality
            
        # 2. Yield Calculation (Linear approx for demo)
        # Assume 1% Ash reduction costs 1.5% Yield (Organic loss) + Contamination
        ash_reduction = feed_ash - target_ash
        yield_loss_pct = ash_reduction * 1.5
        
        theoretical_yield = (100.0 - yield_loss_pct) / 100.0
        
        # Apply Plant Efficiency (Misplacement)
        actual_yield = max(0.0, theoretical_yield * efficiency_factor)
        
        # 3. Product Quality
        # CV usually improves as Ash drops.
        # Approx: 1% Ash drop ~= +0.8 MJ/kg CV increase
        cv_upgrade = ash_reduction * 0.8
        product_cv = feed_cv + cv_upgrade
        
        product_quality = {
            "Ash_ADB": target_ash,
            "CV_ARB": product_cv,
            # Inherit others or recalc
        }
        
        return actual_yield, product_quality

    @staticmethod
    def process_batch(
        plant_config: models_flow.WashPlantConfig,
        feed_force_tonnes: float,
        feed_quality: Dict[str, float]
    ) -> Dict:
        """
        Runs a batch of material through the plant.
        Returns dict with Product Mass/Qual and Reject Mass.
        """
        # Determine target from settings or config
        target_ash = 10.0 # Standard Prime product
        if plant_config.cutpoint_selection_mode == "TargetQuality":
            # In a real app, this would come from a schedule setting or config
            target_ash = 12.0 
            
        yield_frac, prod_qual = WashPlantService.calculate_yield_and_quality(
            feed_quality, 
            target_ash, 
            efficiency_factor=plant_config.yield_adjustment_factor or 1.0
        )
        
        product_tonnes = feed_force_tonnes * yield_frac
        reject_tonnes = feed_force_tonnes - product_tonnes
        
        return {
            "input_tonnes": feed_force_tonnes,
            "yield_fraction": yield_frac,
            "product_tonnes": product_tonnes,
            "product_quality": prod_qual,
            "reject_tonnes": reject_tonnes
        }
