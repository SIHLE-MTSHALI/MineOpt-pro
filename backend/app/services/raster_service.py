"""
Raster Service - Phase 5

Service for handling raster/DEM data including GeoTIFF, ECW, and other formats.

Features:
- Read GeoTIFF, ECW (read-only), JPEG2000
- Extract metadata (extent, resolution, CRS)
- Point sampling / elevation queries
- Generate TIN from DEM
- Tile generation for web display
- Hillshade generation
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import math
import uuid
import datetime
import logging
import os
import io

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import rasterio
    from rasterio.windows import Window
    from rasterio.enums import Resampling
    from rasterio.warp import calculate_default_transform, reproject
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    rasterio = None

from sqlalchemy.orm import Session


# =============================================================================
# Data Classes
# =============================================================================

class RasterFormat(str, Enum):
    """Supported raster formats."""
    GEOTIFF = "geotiff"
    ECW = "ecw"
    JPEG2000 = "jpeg2000"
    MrSID = "mrsid"
    ASCII_GRID = "asc"
    PNG = "png"
    UNKNOWN = "unknown"


@dataclass
class RasterMetadata:
    """Metadata for a raster file."""
    file_path: str
    format: str
    width: int
    height: int
    band_count: int
    dtype: str
    crs_epsg: Optional[int]
    crs_wkt: Optional[str]
    transform: Tuple[float, ...]  # Affine transform
    bounds: Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)
    resolution: Tuple[float, float]  # (x_res, y_res)
    nodata: Optional[float]
    driver: str


@dataclass
class RasterTile:
    """A tile from a raster for web display."""
    tile_x: int
    tile_y: int
    zoom: int
    data: bytes
    format: str  # 'png' or 'jpeg'
    width: int
    height: int


@dataclass
class ElevationSample:
    """Elevation sample at a point."""
    x: float
    y: float
    elevation: Optional[float]
    band: int = 1


@dataclass
class HillshadeParams:
    """Parameters for hillshade generation."""
    azimuth: float = 315.0  # Light source direction (degrees from north)
    altitude: float = 45.0  # Light source elevation (degrees)
    z_factor: float = 1.0   # Vertical exaggeration


# =============================================================================
# Raster Service
# =============================================================================

class RasterService:
    """
    Service for handling raster/DEM data.
    
    Provides:
    - Raster file reading and metadata extraction
    - Point elevation sampling
    - TIN generation from DEM
    - Tile generation for web display
    - Hillshade generation
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize raster service."""
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._check_dependencies()
        
        # Cached raster datasets
        self._cache: Dict[str, Any] = {}
    
    def _check_dependencies(self):
        """Check required dependencies."""
        if not RASTERIO_AVAILABLE:
            self.logger.warning(
                "rasterio not available. Install with: pip install rasterio"
            )
        if not NUMPY_AVAILABLE:
            raise ImportError("numpy is required for raster operations")
    
    # =========================================================================
    # File Operations
    # =========================================================================
    
    def get_metadata(self, file_path: str) -> RasterMetadata:
        """
        Get metadata from a raster file.
        
        Args:
            file_path: Path to raster file
            
        Returns:
            RasterMetadata object
        """
        if not RASTERIO_AVAILABLE:
            raise ImportError("rasterio required for raster operations")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Raster file not found: {file_path}")
        
        with rasterio.open(file_path) as src:
            # Determine format
            driver = src.driver
            raster_format = self._driver_to_format(driver)
            
            # Get CRS info
            crs_epsg = None
            crs_wkt = None
            if src.crs:
                try:
                    crs_epsg = src.crs.to_epsg()
                except:
                    pass
                crs_wkt = src.crs.to_wkt()
            
            return RasterMetadata(
                file_path=file_path,
                format=raster_format.value,
                width=src.width,
                height=src.height,
                band_count=src.count,
                dtype=str(src.dtypes[0]),
                crs_epsg=crs_epsg,
                crs_wkt=crs_wkt,
                transform=tuple(src.transform),
                bounds=src.bounds,
                resolution=(src.res[0], src.res[1]),
                nodata=src.nodata,
                driver=driver
            )
    
    def _driver_to_format(self, driver: str) -> RasterFormat:
        """Convert rasterio driver to format enum."""
        driver_map = {
            "GTiff": RasterFormat.GEOTIFF,
            "ECW": RasterFormat.ECW,
            "JP2OpenJPEG": RasterFormat.JPEG2000,
            "MrSID": RasterFormat.MrSID,
            "AAIGrid": RasterFormat.ASCII_GRID,
            "PNG": RasterFormat.PNG
        }
        return driver_map.get(driver, RasterFormat.UNKNOWN)
    
    def is_readable(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a raster file is readable.
        
        Args:
            file_path: Path to raster file
            
        Returns:
            (success, error_message)
        """
        if not RASTERIO_AVAILABLE:
            return False, "rasterio not installed"
        
        try:
            with rasterio.open(file_path) as src:
                _ = src.read(1, window=Window(0, 0, 1, 1))
            return True, None
        except Exception as e:
            return False, str(e)
    
    # =========================================================================
    # Elevation Sampling
    # =========================================================================
    
    def sample_elevation(
        self,
        file_path: str,
        x: float,
        y: float,
        band: int = 1
    ) -> Optional[float]:
        """
        Sample elevation at a specific XY coordinate.
        
        Args:
            file_path: Path to DEM file
            x, y: Coordinates in raster CRS
            band: Band to sample (1-indexed)
            
        Returns:
            Elevation value or None if outside raster
        """
        if not RASTERIO_AVAILABLE:
            raise ImportError("rasterio required")
        
        with rasterio.open(file_path) as src:
            # Convert coordinates to pixel indices
            row, col = src.index(x, y)
            
            # Check bounds
            if row < 0 or row >= src.height or col < 0 or col >= src.width:
                return None
            
            # Read single pixel
            window = Window(col, row, 1, 1)
            data = src.read(band, window=window)
            value = float(data[0, 0])
            
            # Check nodata
            if src.nodata is not None and value == src.nodata:
                return None
            
            return value
    
    def sample_elevations(
        self,
        file_path: str,
        points: List[Tuple[float, float]],
        band: int = 1
    ) -> List[ElevationSample]:
        """
        Sample elevations at multiple points.
        
        Args:
            file_path: Path to DEM file
            points: List of (x, y) coordinates
            band: Band to sample
            
        Returns:
            List of ElevationSample objects
        """
        results = []
        
        with rasterio.open(file_path) as src:
            for x, y in points:
                try:
                    row, col = src.index(x, y)
                    
                    if 0 <= row < src.height and 0 <= col < src.width:
                        window = Window(col, row, 1, 1)
                        data = src.read(band, window=window)
                        value = float(data[0, 0])
                        
                        if src.nodata is not None and value == src.nodata:
                            value = None
                    else:
                        value = None
                except:
                    value = None
                
                results.append(ElevationSample(x=x, y=y, elevation=value, band=band))
        
        return results
    
    def sample_along_line(
        self,
        file_path: str,
        start: Tuple[float, float],
        end: Tuple[float, float],
        interval: float,
        band: int = 1
    ) -> List[ElevationSample]:
        """
        Sample elevations along a line at regular intervals.
        
        Args:
            file_path: Path to DEM file
            start: Start point (x, y)
            end: End point (x, y)
            interval: Sampling interval
            band: Band to sample
            
        Returns:
            List of ElevationSample objects
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < interval:
            return self.sample_elevations(file_path, [start, end], band)
        
        # Generate points along line
        n_samples = int(distance / interval) + 1
        points = []
        for i in range(n_samples):
            t = i / (n_samples - 1) if n_samples > 1 else 0
            x = start[0] + t * dx
            y = start[1] + t * dy
            points.append((x, y))
        
        return self.sample_elevations(file_path, points, band)
    
    # =========================================================================
    # TIN Generation
    # =========================================================================
    
    def generate_tin_from_dem(
        self,
        file_path: str,
        sample_spacing: float,
        band: int = 1,
        boundary: Optional[List[Tuple[float, float]]] = None
    ) -> Dict[str, Any]:
        """
        Generate TIN surface from DEM raster.
        
        Args:
            file_path: Path to DEM file
            sample_spacing: Grid sampling spacing
            band: Band to use
            boundary: Optional boundary polygon
            
        Returns:
            Dict with 'vertices' and 'triangles' for TIN
        """
        if not RASTERIO_AVAILABLE or not NUMPY_AVAILABLE:
            raise ImportError("rasterio and numpy required")
        
        from scipy.spatial import Delaunay
        
        metadata = self.get_metadata(file_path)
        
        # Calculate sample grid
        min_x, min_y, max_x, max_y = metadata.bounds
        
        nx = int((max_x - min_x) / sample_spacing) + 1
        ny = int((max_y - min_y) / sample_spacing) + 1
        
        # Sample DEM at grid points
        points = []
        with rasterio.open(file_path) as src:
            for i in range(nx):
                for j in range(ny):
                    x = min_x + i * sample_spacing
                    y = min_y + j * sample_spacing
                    
                    # Check boundary if provided
                    if boundary and not self._point_in_polygon(x, y, boundary):
                        continue
                    
                    try:
                        row, col = src.index(x, y)
                        if 0 <= row < src.height and 0 <= col < src.width:
                            window = Window(col, row, 1, 1)
                            data = src.read(band, window=window)
                            z = float(data[0, 0])
                            
                            if src.nodata is None or z != src.nodata:
                                points.append((x, y, z))
                    except:
                        continue
        
        if len(points) < 3:
            raise ValueError("Not enough valid points for triangulation")
        
        # Triangulate
        pts_2d = np.array([(p[0], p[1]) for p in points])
        tri = Delaunay(pts_2d)
        
        return {
            "vertices": points,
            "triangles": [tuple(int(v) for v in s) for s in tri.simplices],
            "vertex_count": len(points),
            "triangle_count": len(tri.simplices),
            "bounds": metadata.bounds,
            "sample_spacing": sample_spacing
        }
    
    # =========================================================================
    # Tile Generation
    # =========================================================================
    
    def generate_overview_image(
        self,
        file_path: str,
        max_size: int = 512,
        band: int = 1
    ) -> bytes:
        """
        Generate a downsampled overview image of the raster.
        
        Args:
            file_path: Path to raster file
            max_size: Maximum dimension of output
            band: Band to use for single-band rasters
            
        Returns:
            PNG image bytes
        """
        if not RASTERIO_AVAILABLE or not NUMPY_AVAILABLE:
            raise ImportError("rasterio and numpy required")
        
        from PIL import Image
        
        with rasterio.open(file_path) as src:
            # Calculate output size maintaining aspect ratio
            if src.width > src.height:
                out_width = max_size
                out_height = int(max_size * src.height / src.width)
            else:
                out_height = max_size
                out_width = int(max_size * src.width / src.height)
            
            # Read resampled data
            if src.count >= 3:
                # RGB image
                data = src.read(
                    [1, 2, 3],
                    out_shape=(3, out_height, out_width),
                    resampling=Resampling.bilinear
                )
                # Transpose to (height, width, channels)
                img_array = np.transpose(data, (1, 2, 0))
            else:
                # Single band - create grayscale
                data = src.read(
                    band,
                    out_shape=(out_height, out_width),
                    resampling=Resampling.bilinear
                )
                
                # Normalize to 0-255
                valid = data[data != src.nodata] if src.nodata else data
                if len(valid) > 0:
                    vmin, vmax = np.percentile(valid, [2, 98])
                    data = np.clip((data - vmin) / (vmax - vmin) * 255, 0, 255)
                    data = data.astype(np.uint8)
                else:
                    data = np.zeros((out_height, out_width), dtype=np.uint8)
                
                img_array = data
            
            # Convert to PIL Image and save as PNG
            if len(img_array.shape) == 3:
                img = Image.fromarray(img_array.astype(np.uint8), mode='RGB')
            else:
                img = Image.fromarray(img_array, mode='L')
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()
    
    def generate_tile(
        self,
        file_path: str,
        tile_x: int,
        tile_y: int,
        zoom: int,
        tile_size: int = 256
    ) -> RasterTile:
        """
        Generate a map tile at specified TMS coordinates.
        
        Args:
            file_path: Path to raster file
            tile_x, tile_y: Tile coordinates
            zoom: Zoom level
            tile_size: Tile size in pixels
            
        Returns:
            RasterTile object
        """
        if not RASTERIO_AVAILABLE or not NUMPY_AVAILABLE:
            raise ImportError("rasterio and numpy required")
        
        from PIL import Image
        
        # Calculate tile bounds in CRS coordinates
        # This is a simplified implementation - would need proper projection handling
        metadata = self.get_metadata(file_path)
        min_x, min_y, max_x, max_y = metadata.bounds
        
        width = max_x - min_x
        height = max_y - min_y
        
        n_tiles = 2 ** zoom
        tile_width = width / n_tiles
        tile_height = height / n_tiles
        
        tile_min_x = min_x + tile_x * tile_width
        tile_max_x = tile_min_x + tile_width
        tile_max_y = max_y - tile_y * tile_height  # Y is inverted
        tile_min_y = tile_max_y - tile_height
        
        with rasterio.open(file_path) as src:
            # Calculate window in pixel coordinates
            col_start = int((tile_min_x - min_x) / metadata.resolution[0])
            row_start = int((max_y - tile_max_y) / metadata.resolution[1])
            col_end = int((tile_max_x - min_x) / metadata.resolution[0])
            row_end = int((max_y - tile_min_y) / metadata.resolution[1])
            
            # Clamp to valid range
            col_start = max(0, min(col_start, src.width - 1))
            col_end = max(col_start + 1, min(col_end, src.width))
            row_start = max(0, min(row_start, src.height - 1))
            row_end = max(row_start + 1, min(row_end, src.height))
            
            window = Window(col_start, row_start, col_end - col_start, row_end - row_start)
            
            # Read and resample
            if src.count >= 3:
                data = src.read(
                    [1, 2, 3],
                    window=window,
                    out_shape=(3, tile_size, tile_size),
                    resampling=Resampling.bilinear
                )
                img_array = np.transpose(data, (1, 2, 0))
                img = Image.fromarray(img_array.astype(np.uint8), mode='RGB')
            else:
                data = src.read(
                    1,
                    window=window,
                    out_shape=(tile_size, tile_size),
                    resampling=Resampling.bilinear
                )
                
                # Normalize
                valid = data[data != src.nodata] if src.nodata else data.flatten()
                if len(valid) > 0:
                    vmin, vmax = np.percentile(valid, [2, 98])
                    data = np.clip((data - vmin) / (vmax - vmin) * 255, 0, 255)
                
                img = Image.fromarray(data.astype(np.uint8), mode='L')
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            
            return RasterTile(
                tile_x=tile_x,
                tile_y=tile_y,
                zoom=zoom,
                data=buffer.getvalue(),
                format='png',
                width=tile_size,
                height=tile_size
            )
    
    # =========================================================================
    # Hillshade
    # =========================================================================
    
    def generate_hillshade(
        self,
        file_path: str,
        params: Optional[HillshadeParams] = None,
        output_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate hillshade from DEM.
        
        Args:
            file_path: Path to DEM file
            params: Hillshade parameters
            output_path: Optional output file path
            
        Returns:
            Hillshade array (0-255)
        """
        if not RASTERIO_AVAILABLE or not NUMPY_AVAILABLE:
            raise ImportError("rasterio and numpy required")
        
        params = params or HillshadeParams()
        
        with rasterio.open(file_path) as src:
            elevation = src.read(1).astype(float)
            res = src.res[0]  # Assume square pixels
            
            # Handle nodata
            if src.nodata is not None:
                elevation[elevation == src.nodata] = np.nan
        
        # Calculate gradients
        dy, dx = np.gradient(elevation * params.z_factor, res)
        
        # Convert angles to radians
        azimuth_rad = np.radians(params.azimuth)
        altitude_rad = np.radians(params.altitude)
        
        # Calculate slope and aspect
        slope = np.arctan(np.sqrt(dx**2 + dy**2))
        aspect = np.arctan2(-dx, dy)
        
        # Calculate hillshade
        hillshade = (
            np.sin(altitude_rad) * np.cos(slope) +
            np.cos(altitude_rad) * np.sin(slope) * 
            np.cos(azimuth_rad - aspect)
        )
        
        # Scale to 0-255
        hillshade = np.clip(hillshade * 255, 0, 255).astype(np.uint8)
        
        # Handle nodata
        hillshade[np.isnan(elevation)] = 0
        
        if output_path:
            # Save as GeoTIFF
            with rasterio.open(file_path) as src:
                profile = src.profile.copy()
                profile.update(dtype=rasterio.uint8, count=1)
                
                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(hillshade, 1)
        
        return hillshade
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _point_in_polygon(
        self,
        x: float,
        y: float,
        polygon: List[Tuple[float, float]]
    ) -> bool:
        """Ray casting algorithm for point in polygon test."""
        n = len(polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
    
    def get_supported_formats(self) -> List[Dict[str, str]]:
        """Get list of supported raster formats."""
        formats = [
            {"format": "geotiff", "extensions": [".tif", ".tiff"], "writable": True},
            {"format": "ecw", "extensions": [".ecw"], "writable": False},
            {"format": "jpeg2000", "extensions": [".jp2", ".j2k"], "writable": True},
            {"format": "mrsid", "extensions": [".sid"], "writable": False},
            {"format": "ascii_grid", "extensions": [".asc"], "writable": True},
            {"format": "png", "extensions": [".png"], "writable": True}
        ]
        return formats


# =============================================================================
# Factory Function
# =============================================================================

def get_raster_service(db: Optional[Session] = None) -> RasterService:
    """Get raster service instance."""
    return RasterService(db)
