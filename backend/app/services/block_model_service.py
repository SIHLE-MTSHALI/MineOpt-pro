"""
Block Model Service - Phase 3 Block Model with Kriging

Service for creating and estimating block models:
- Define block model grids
- Generate blocks from borehole data
- Estimate grades using kriging or IDW
- Create activity areas from block groups
- Generate parcels from blocks

Integrates with KrigingService for grade estimation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from .kriging_service import (
    get_kriging_service, 
    KrigingService, 
    SamplePoint, 
    VariogramParams,
    VariogramModel,
    BlockEstimate
)
from ..domain.models_block_model import BlockModelDefinition, Block, BlockModelRun
from ..domain.models_borehole import BoreholeCollar, BoreholeInterval
from ..domain.models_resource import ActivityArea, MaterialType


@dataclass
class BlockModelConfig:
    """Configuration for creating a block model."""
    name: str
    site_id: str
    
    # Grid origin (auto-calculated from data if None)
    origin_x: Optional[float] = None
    origin_y: Optional[float] = None
    origin_z: Optional[float] = None
    
    # Block dimensions
    block_size_x: float = 10.0
    block_size_y: float = 10.0
    block_size_z: float = 5.0
    
    # Grid extent (auto-calculated if None)
    count_x: Optional[int] = None
    count_y: Optional[int] = None
    count_z: Optional[int] = None
    
    # Padding around data (meters)
    padding: float = 50.0
    
    description: str = ""


@dataclass
class EstimationConfig:
    """Configuration for grade estimation."""
    quality_field: str
    method: str = "kriging"  # kriging, idw
    
    # Variogram settings
    variogram_model: VariogramModel = VariogramModel.SPHERICAL
    auto_fit_variogram: bool = True
    
    # Search parameters
    max_samples: int = 20
    min_samples: int = 3
    search_radius: Optional[float] = None
    
    # IDW settings
    idw_power: float = 2.0
    
    # Cross-validation
    run_cross_validation: bool = True


@dataclass 
class BlockModelResult:
    """Result of block model creation/estimation."""
    success: bool
    model_id: Optional[str] = None
    run_id: Optional[str] = None
    blocks_created: int = 0
    blocks_estimated: int = 0
    variogram_params: Optional[VariogramParams] = None
    cv_rmse: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BlockModelService:
    """
    Service for block model creation and estimation.
    
    Provides:
    - Create block model grids from borehole extents
    - Composite borehole data for estimation
    - Estimate grades using kriging or IDW
    - Track estimation runs with parameters
    - Create activity areas from blocks
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.kriging = get_kriging_service()
    
    # =========================================================================
    # BLOCK MODEL CREATION
    # =========================================================================
    
    def create_block_model(
        self,
        config: BlockModelConfig,
        collar_ids: Optional[List[str]] = None
    ) -> BlockModelResult:
        """
        Create a new block model definition.
        
        If collar_ids provided, auto-calculates extent from borehole data.
        
        Args:
            config: Block model configuration
            collar_ids: Optional list of borehole IDs to use for extent
            
        Returns:
            BlockModelResult with model_id
        """
        result = BlockModelResult(success=False)
        
        try:
            # Get extent from boreholes if needed
            if collar_ids:
                extent = self._calculate_extent_from_boreholes(collar_ids)
                if extent:
                    min_x, min_y, min_z, max_x, max_y, max_z = extent
                    
                    # Apply padding
                    if config.origin_x is None:
                        config.origin_x = min_x - config.padding
                    if config.origin_y is None:
                        config.origin_y = min_y - config.padding
                    if config.origin_z is None:
                        config.origin_z = min_z - config.padding
                    
                    # Calculate counts
                    if config.count_x is None:
                        range_x = (max_x + config.padding) - config.origin_x
                        config.count_x = int(range_x / config.block_size_x) + 1
                    if config.count_y is None:
                        range_y = (max_y + config.padding) - config.origin_y
                        config.count_y = int(range_y / config.block_size_y) + 1
                    if config.count_z is None:
                        range_z = (max_z + config.padding) - config.origin_z
                        config.count_z = int(range_z / config.block_size_z) + 1
            
            # Validate required fields
            if config.origin_x is None or config.origin_y is None or config.origin_z is None:
                result.errors.append("Origin coordinates required")
                return result
            
            if config.count_x is None or config.count_y is None or config.count_z is None:
                result.errors.append("Grid counts required")
                return result
            
            # Create block model definition
            model = BlockModelDefinition(
                site_id=config.site_id,
                name=config.name,
                description=config.description,
                origin_x=config.origin_x,
                origin_y=config.origin_y,
                origin_z=config.origin_z,
                block_size_x=config.block_size_x,
                block_size_y=config.block_size_y,
                block_size_z=config.block_size_z,
                count_x=config.count_x,
                count_y=config.count_y,
                count_z=config.count_z,
                status="Draft"
            )
            
            self.db.add(model)
            self.db.flush()
            
            # Generate blocks
            blocks_created = self._generate_blocks(model)
            
            self.db.commit()
            
            result.success = True
            result.model_id = model.model_id
            result.blocks_created = blocks_created
            
        except Exception as e:
            self.db.rollback()
            result.errors.append(f"Failed to create block model: {str(e)}")
        
        return result
    
    def _calculate_extent_from_boreholes(
        self,
        collar_ids: List[str]
    ) -> Optional[Tuple[float, float, float, float, float, float]]:
        """Calculate extent from borehole intervals."""
        intervals = self.db.query(BoreholeInterval).filter(
            BoreholeInterval.collar_id.in_(collar_ids)
        ).all()
        
        if not intervals:
            # Fall back to collars
            collars = self.db.query(BoreholeCollar).filter(
                BoreholeCollar.collar_id.in_(collar_ids)
            ).all()
            
            if not collars:
                return None
            
            xs = [c.easting for c in collars]
            ys = [c.northing for c in collars]
            zs = [c.elevation for c in collars]
            z_bottoms = [c.elevation - (c.total_depth or 0) for c in collars]
            
            return (min(xs), min(ys), min(z_bottoms), max(xs), max(ys), max(zs))
        
        # Use interval centroids
        xs = [i.calc_easting for i in intervals if i.calc_easting]
        ys = [i.calc_northing for i in intervals if i.calc_northing]
        zs = [i.calc_elevation for i in intervals if i.calc_elevation]
        
        if not xs:
            return None
        
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))
    
    def _generate_blocks(self, model: BlockModelDefinition) -> int:
        """Generate block records for the model."""
        count = 0
        
        for i in range(model.count_x):
            for j in range(model.count_y):
                for k in range(model.count_z):
                    cx, cy, cz = model.get_block_centroid(i, j, k)
                    
                    block = Block(
                        model_id=model.model_id,
                        i=i,
                        j=j,
                        k=k,
                        centroid_x=cx,
                        centroid_y=cy,
                        centroid_z=cz,
                        volume_bcm=model.block_size_x * model.block_size_y * model.block_size_z
                    )
                    self.db.add(block)
                    count += 1
        
        return count
    
    # =========================================================================
    # GRADE ESTIMATION
    # =========================================================================
    
    def estimate_grades(
        self,
        model_id: str,
        collar_ids: List[str],
        config: EstimationConfig
    ) -> BlockModelResult:
        """
        Estimate grades for all blocks in a model.
        
        Args:
            model_id: Block model ID
            collar_ids: Borehole collars to use as sample data
            config: Estimation configuration
            
        Returns:
            BlockModelResult with estimation statistics
        """
        result = BlockModelResult(success=False, model_id=model_id)
        start_time = datetime.utcnow()
        
        try:
            # Get model
            model = self.db.query(BlockModelDefinition).filter(
                BlockModelDefinition.model_id == model_id
            ).first()
            
            if not model:
                result.errors.append("Block model not found")
                return result
            
            # Get sample data from boreholes
            samples = self._get_samples_from_boreholes(collar_ids, config.quality_field)
            
            if len(samples) < config.min_samples:
                result.errors.append(f"Insufficient samples: {len(samples)} < {config.min_samples}")
                return result
            
            # Fit variogram if using kriging
            variogram_params = None
            if config.method == "kriging":
                if config.auto_fit_variogram:
                    variogram_params = self.kriging.auto_fit_variogram(samples)
                else:
                    experimental = self.kriging.calculate_experimental_variogram(samples)
                    variogram_params = self.kriging.fit_variogram(
                        experimental, 
                        config.variogram_model
                    )
                result.variogram_params = variogram_params
            
            # Cross-validation
            if config.run_cross_validation:
                cv_rmse = self.kriging.cross_validate(
                    samples, 
                    variogram_params,
                    config.method
                )
                result.cv_rmse = cv_rmse
            
            # Get blocks
            blocks = self.db.query(Block).filter(
                Block.model_id == model_id
            ).all()
            
            # Prepare target points
            target_points = [
                (b.centroid_x, b.centroid_y, b.centroid_z) 
                for b in blocks
            ]
            
            # Estimate
            if config.method == "kriging":
                estimates = self.kriging.ordinary_kriging(
                    samples,
                    target_points,
                    variogram_params,
                    config.max_samples,
                    config.min_samples,
                    config.search_radius
                )
            else:
                estimates = self.kriging.inverse_distance_weighting(
                    samples,
                    target_points,
                    config.idw_power,
                    config.max_samples,
                    config.search_radius
                )
            
            # Update blocks with estimates
            values = []
            for block, estimate in zip(blocks, estimates):
                # Update quality vector
                if block.quality_vector is None:
                    block.quality_vector = {}
                block.quality_vector[config.quality_field] = estimate.estimated_value
                
                # Set as primary if first estimation
                if block.primary_field is None:
                    block.primary_field = config.quality_field
                    block.primary_value = estimate.estimated_value
                
                block.estimation_method = estimate.estimation_method
                block.estimation_variance = estimate.estimation_variance
                block.num_samples = estimate.num_samples
                block.updated_at = datetime.utcnow()
                
                values.append(estimate.estimated_value)
            
            result.blocks_estimated = len(blocks)
            
            # Create run record
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            import numpy as np
            values_array = np.array(values)
            
            run = BlockModelRun(
                model_id=model_id,
                run_name=f"{config.quality_field}_{config.method}",
                quality_field=config.quality_field,
                method=config.method,
                variogram_model=variogram_params.model.value if variogram_params else None,
                variogram_nugget=variogram_params.nugget if variogram_params else None,
                variogram_sill=variogram_params.sill if variogram_params else None,
                variogram_range=variogram_params.range if variogram_params else None,
                variogram_r_squared=variogram_params.r_squared if variogram_params else None,
                max_samples=config.max_samples,
                min_samples=config.min_samples,
                search_radius=config.search_radius,
                idw_power=config.idw_power if config.method == "idw" else None,
                blocks_estimated=len(blocks),
                mean_value=float(np.mean(values_array)),
                min_value=float(np.min(values_array)),
                max_value=float(np.max(values_array)),
                std_dev=float(np.std(values_array)),
                cv_rmse=result.cv_rmse,
                num_samples_used=len(samples),
                sample_source="boreholes",
                status="Completed",
                started_at=start_time,
                completed_at=end_time,
                duration_seconds=duration
            )
            self.db.add(run)
            
            # Update model status
            model.status = "Estimated"
            model.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            result.success = True
            result.run_id = run.run_id
            
        except Exception as e:
            self.db.rollback()
            result.errors.append(f"Estimation failed: {str(e)}")
        
        return result
    
    def _get_samples_from_boreholes(
        self,
        collar_ids: List[str],
        quality_field: str
    ) -> List[SamplePoint]:
        """Extract sample points from borehole intervals."""
        samples = []
        
        intervals = self.db.query(BoreholeInterval).filter(
            BoreholeInterval.collar_id.in_(collar_ids)
        ).all()
        
        for interval in intervals:
            if interval.quality_vector and quality_field in interval.quality_vector:
                value = interval.quality_vector[quality_field]
                
                # Use calculated coordinates if available
                if interval.calc_easting and interval.calc_northing and interval.calc_elevation:
                    x = interval.calc_easting
                    y = interval.calc_northing
                    z = interval.calc_elevation
                else:
                    # Fall back to collar with depth adjustment
                    collar = self.db.query(BoreholeCollar).filter(
                        BoreholeCollar.collar_id == interval.collar_id
                    ).first()
                    
                    if collar:
                        x = collar.easting
                        y = collar.northing
                        mid_depth = (interval.from_depth + interval.to_depth) / 2
                        z = collar.elevation - mid_depth
                    else:
                        continue
                
                samples.append(SamplePoint(
                    x=x,
                    y=y,
                    z=z,
                    value=value,
                    hole_id=interval.collar_id
                ))
        
        return samples
    
    # =========================================================================
    # BLOCK MODEL QUERIES
    # =========================================================================
    
    def get_model(self, model_id: str) -> Optional[BlockModelDefinition]:
        """Get a block model by ID."""
        return self.db.query(BlockModelDefinition).filter(
            BlockModelDefinition.model_id == model_id
        ).first()
    
    def get_blocks(
        self,
        model_id: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        quality_field: Optional[str] = None,
        material_type_id: Optional[str] = None
    ) -> List[Block]:
        """
        Get blocks with optional filtering.
        
        Args:
            model_id: Block model ID
            min_value: Minimum primary value
            max_value: Maximum primary value
            quality_field: Filter by specific quality field
            material_type_id: Filter by material type
            
        Returns:
            List of matching blocks
        """
        query = self.db.query(Block).filter(Block.model_id == model_id)
        
        if min_value is not None:
            query = query.filter(Block.primary_value >= min_value)
        if max_value is not None:
            query = query.filter(Block.primary_value <= max_value)
        if material_type_id:
            query = query.filter(Block.material_type_id == material_type_id)
        
        return query.all()
    
    def get_blocks_for_visualization(
        self,
        model_id: str,
        quality_field: Optional[str] = None,
        k_level: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get blocks formatted for 3D visualization.
        
        Args:
            model_id: Block model ID
            quality_field: Which field to use for coloring
            k_level: Optional specific Z level
            
        Returns:
            List of block dicts with coordinates and values
        """
        query = self.db.query(Block).filter(Block.model_id == model_id)
        
        if k_level is not None:
            query = query.filter(Block.k == k_level)
        
        blocks = query.all()
        
        result = []
        for b in blocks:
            value = b.primary_value
            if quality_field and b.quality_vector:
                value = b.quality_vector.get(quality_field, b.primary_value)
            
            result.append({
                "block_id": b.block_id,
                "i": b.i,
                "j": b.j,
                "k": b.k,
                "x": b.centroid_x,
                "y": b.centroid_y,
                "z": b.centroid_z,
                "value": value,
                "variance": b.estimation_variance,
                "material_type_id": b.material_type_id,
                "is_mineable": b.is_mineable
            })
        
        return result
    
    # =========================================================================
    # ACTIVITY AREA GENERATION
    # =========================================================================
    
    def create_activity_areas_from_blocks(
        self,
        model_id: str,
        min_value: float,
        max_value: Optional[float] = None,
        activity_type: str = "Coal Mining",
        seam_name: Optional[str] = None
    ) -> List[str]:
        """
        Create activity areas from blocks meeting quality criteria.
        
        Groups adjacent blocks into activity areas for scheduling.
        
        Args:
            model_id: Block model ID
            min_value: Minimum quality value
            max_value: Maximum quality value (optional)
            activity_type: Type of activity
            seam_name: Optional seam name for grouping
            
        Returns:
            List of created activity area IDs
        """
        # Get qualifying blocks
        query = self.db.query(Block).filter(
            Block.model_id == model_id,
            Block.primary_value >= min_value,
            Block.is_mineable == True
        )
        
        if max_value is not None:
            query = query.filter(Block.primary_value <= max_value)
        
        blocks = query.all()
        
        if not blocks:
            return []
        
        # Get model for site_id
        model = self.get_model(model_id)
        if not model:
            return []
        
        # Group blocks by k-level (bench)
        levels: Dict[int, List[Block]] = {}
        for b in blocks:
            if b.k not in levels:
                levels[b.k] = []
            levels[b.k].append(b)
        
        area_ids = []
        
        for k_level, level_blocks in levels.items():
            # Create one activity area per level for now
            # TODO: Implement proper polygon grouping
            
            # Calculate bounding polygon
            xs = [b.centroid_x for b in level_blocks]
            ys = [b.centroid_y for b in level_blocks]
            zs = [b.centroid_z for b in level_blocks]
            
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            avg_z = sum(zs) / len(zs)
            
            # Simple bounding box geometry
            vertices = [
                [min_x - model.block_size_x/2, min_y - model.block_size_y/2, avg_z],
                [max_x + model.block_size_x/2, min_y - model.block_size_y/2, avg_z],
                [max_x + model.block_size_x/2, max_y + model.block_size_y/2, avg_z],
                [min_x - model.block_size_x/2, max_y + model.block_size_y/2, avg_z],
            ]
            
            # Calculate totals
            total_tonnes = sum(b.tonnes or 0 for b in level_blocks)
            avg_value = sum(b.primary_value or 0 for b in level_blocks) / len(level_blocks)
            
            # Create activity area
            area = ActivityArea(
                site_id=model.site_id,
                name=f"{seam_name or 'Block'}_Level_{k_level}",
                activity_type=activity_type,
                geometry={
                    "vertices": vertices,
                    "source": "block_model",
                    "model_id": model_id,
                    "k_level": k_level
                },
                total_tonnes=total_tonnes,
                remaining_tonnes=total_tonnes
            )
            self.db.add(area)
            self.db.flush()
            
            # Link blocks to area
            for b in level_blocks:
                b.linked_activity_area_id = area.area_id
            
            area_ids.append(area.area_id)
        
        self.db.commit()
        return area_ids


def get_block_model_service(db: Session) -> BlockModelService:
    """Get a block model service instance."""
    return BlockModelService(db)
