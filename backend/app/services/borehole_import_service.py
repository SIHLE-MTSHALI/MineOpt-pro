"""
Borehole Import Service - Phase 2 Borehole Data Workflows

Service for importing borehole data from various file formats:
- Vulcan (separate collar/survey/assay CSV files)
- Minex (CSV with format file concepts)
- Surpac (CSV exports)
- GeoBank (CSV/TXT exports)
- Generic CSV

Features:
- Parse and validate borehole data
- Calculate 3D traces from surveys
- Generate quality vectors from assays
- Support batch imports
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import math
from sqlalchemy.orm import Session

from .tabular_parser import get_tabular_parser, TabularParseResult, BoreholeBoreholePurpose
from ..domain.models_borehole import (
    BoreholeCollar, BoreholeSurvey, BoreholeInterval, 
    BoreholeAssay, Borehole3DTrace
)


@dataclass
class ImportValidationError:
    """An error found during import validation."""
    hole_id: str
    field: str
    message: str
    row_number: Optional[int] = None
    severity: str = "error"  # error, warning


@dataclass
class BoreholeImportResult:
    """Result of a borehole import operation."""
    success: bool
    collars_imported: int = 0
    surveys_imported: int = 0
    intervals_imported: int = 0
    assays_imported: int = 0
    traces_calculated: int = 0
    errors: List[ImportValidationError] = field(default_factory=list)
    warnings: List[ImportValidationError] = field(default_factory=list)
    collar_ids: List[str] = field(default_factory=list)


@dataclass
class CollarRecord:
    """Parsed collar record before database insertion."""
    hole_id: str
    easting: float
    northing: float
    elevation: float
    total_depth: Optional[float] = None
    azimuth: float = 0.0
    dip: float = -90.0
    hole_type: str = "Exploration"
    row_number: int = 0


@dataclass
class SurveyRecord:
    """Parsed survey record before database insertion."""
    hole_id: str
    depth: float
    azimuth: float
    dip: float
    row_number: int = 0


@dataclass
class IntervalRecord:
    """Parsed interval/assay record before database insertion."""
    hole_id: str
    from_depth: float
    to_depth: float
    seam_name: Optional[str] = None
    lithology_code: Optional[str] = None
    quality_values: Dict[str, float] = field(default_factory=dict)
    row_number: int = 0


class BoreholeImportService:
    """
    Service for importing borehole data from multiple formats.
    
    Supports:
    - Loading collar, survey, and assay data from separate files
    - Validating relationships between data
    - Calculating 3D traces from deviation surveys
    - Persisting to database
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.parser = get_tabular_parser()
    
    # =========================================================================
    # PARSING METHODS
    # =========================================================================
    
    def parse_collar_file(
        self,
        content: bytes,
        filename: str,
        column_mappings: Optional[Dict[str, str]] = None
    ) -> Tuple[List[CollarRecord], List[ImportValidationError]]:
        """
        Parse a collar file and extract records.
        
        Args:
            content: File content as bytes
            filename: Original filename
            column_mappings: Optional custom column mappings
            
        Returns:
            Tuple of (records, errors)
        """
        result = self.parser.parse_bytes(content, filename)
        
        if not result.success:
            return [], [ImportValidationError(
                hole_id="",
                field="",
                message=f"Failed to parse file: {result.errors[0] if result.errors else 'Unknown error'}"
            )]
        
        # Build mappings
        mappings = self._build_collar_mappings(result, column_mappings)
        
        # Extract records
        records = []
        errors = []
        
        for row in result.rows:
            try:
                record = self._parse_collar_row(row.values, mappings, row.row_number)
                if record:
                    records.append(record)
            except Exception as e:
                errors.append(ImportValidationError(
                    hole_id=row.values.get(mappings.get("HoleID", "HoleID"), "Unknown"),
                    field="parse",
                    message=str(e),
                    row_number=row.row_number
                ))
        
        return records, errors
    
    def parse_survey_file(
        self,
        content: bytes,
        filename: str,
        column_mappings: Optional[Dict[str, str]] = None
    ) -> Tuple[List[SurveyRecord], List[ImportValidationError]]:
        """Parse a survey file and extract records."""
        result = self.parser.parse_bytes(content, filename)
        
        if not result.success:
            return [], [ImportValidationError(
                hole_id="",
                field="",
                message=f"Failed to parse file: {result.errors[0] if result.errors else 'Unknown error'}"
            )]
        
        mappings = self._build_survey_mappings(result, column_mappings)
        
        records = []
        errors = []
        
        for row in result.rows:
            try:
                record = self._parse_survey_row(row.values, mappings, row.row_number)
                if record:
                    records.append(record)
            except Exception as e:
                errors.append(ImportValidationError(
                    hole_id=row.values.get(mappings.get("HoleID", "HoleID"), "Unknown"),
                    field="parse",
                    message=str(e),
                    row_number=row.row_number
                ))
        
        return records, errors
    
    def parse_assay_file(
        self,
        content: bytes,
        filename: str,
        column_mappings: Optional[Dict[str, str]] = None,
        quality_columns: Optional[List[str]] = None
    ) -> Tuple[List[IntervalRecord], List[ImportValidationError]]:
        """
        Parse an assay file and extract records.
        
        Args:
            quality_columns: List of column names that contain quality values
        """
        result = self.parser.parse_bytes(content, filename)
        
        if not result.success:
            return [], [ImportValidationError(
                hole_id="",
                field="",
                message=f"Failed to parse file: {result.errors[0] if result.errors else 'Unknown error'}"
            )]
        
        mappings = self._build_assay_mappings(result, column_mappings)
        
        # Detect quality columns if not specified
        if quality_columns is None:
            quality_columns = self._detect_quality_columns(result)
        
        records = []
        errors = []
        
        for row in result.rows:
            try:
                record = self._parse_assay_row(
                    row.values, mappings, quality_columns, row.row_number
                )
                if record:
                    records.append(record)
            except Exception as e:
                errors.append(ImportValidationError(
                    hole_id=row.values.get(mappings.get("HoleID", "HoleID"), "Unknown"),
                    field="parse",
                    message=str(e),
                    row_number=row.row_number
                ))
        
        return records, errors
    
    def _build_collar_mappings(
        self, 
        result: TabularParseResult,
        custom: Optional[Dict[str, str]]
    ) -> Dict[str, str]:
        """Build column mappings for collar file."""
        mappings = {}
        
        # Start with suggested mappings
        for col in result.columns:
            if col.suggested_mapping:
                mappings[col.suggested_mapping] = col.name
        
        # Override with custom mappings
        if custom:
            for target, source in custom.items():
                mappings[target] = source
        
        # Ensure required fields have mappings
        required = ["HoleID", "Easting", "Northing", "Elevation"]
        for field in required:
            if field not in mappings:
                # Try to find a likely column
                for col in result.columns:
                    if field.upper() in col.name.upper():
                        mappings[field] = col.name
                        break
        
        return mappings
    
    def _build_survey_mappings(
        self,
        result: TabularParseResult,
        custom: Optional[Dict[str, str]]
    ) -> Dict[str, str]:
        """Build column mappings for survey file."""
        mappings = {}
        
        for col in result.columns:
            if col.suggested_mapping:
                mappings[col.suggested_mapping] = col.name
        
        if custom:
            for target, source in custom.items():
                mappings[target] = source
        
        return mappings
    
    def _build_assay_mappings(
        self,
        result: TabularParseResult,
        custom: Optional[Dict[str, str]]
    ) -> Dict[str, str]:
        """Build column mappings for assay file."""
        mappings = {}
        
        for col in result.columns:
            if col.suggested_mapping:
                mappings[col.suggested_mapping] = col.name
        
        if custom:
            for target, source in custom.items():
                mappings[target] = source
        
        return mappings
    
    def _detect_quality_columns(self, result: TabularParseResult) -> List[str]:
        """Detect which columns contain quality values."""
        quality_keywords = [
            "CV", "ASH", "MOISTURE", "SULPHUR", "VM", "FC", "RD", "YIELD",
            "TS", "IM", "TM", "HGI", "PHOSPHORUS", "SODIUM"
        ]
        
        quality_cols = []
        for col in result.columns:
            col_upper = col.name.upper()
            
            # Skip known non-quality columns
            if col_upper in ["HOLEID", "HOLE_ID", "FROM", "TO", "SEAM", "SAMPLE"]:
                continue
            
            # Check if column name contains a quality keyword
            for keyword in quality_keywords:
                if keyword in col_upper:
                    quality_cols.append(col.name)
                    break
            else:
                # Also include numeric columns that could be quality values
                from .tabular_parser import ColumnType
                if col.inferred_type == ColumnType.FLOAT:
                    # Check if values are in reasonable quality ranges
                    if col.min_value is not None and col.max_value is not None:
                        if 0 <= col.min_value and col.max_value <= 100:
                            quality_cols.append(col.name)
        
        return quality_cols
    
    def _parse_collar_row(
        self, 
        values: Dict[str, str],
        mappings: Dict[str, str],
        row_number: int
    ) -> Optional[CollarRecord]:
        """Parse a single collar row."""
        hole_id = values.get(mappings.get("HoleID", "HoleID"), "").strip()
        if not hole_id:
            return None
        
        easting = float(values.get(mappings.get("Easting", "Easting"), 0))
        northing = float(values.get(mappings.get("Northing", "Northing"), 0))
        elevation = float(values.get(mappings.get("Elevation", "Elevation"), 0))
        
        total_depth = None
        depth_str = values.get(mappings.get("TotalDepth", "TotalDepth"), "")
        if depth_str:
            try:
                total_depth = float(depth_str)
            except ValueError:
                pass
        
        azimuth = 0.0
        az_str = values.get(mappings.get("Azimuth", "Azimuth"), "")
        if az_str:
            try:
                azimuth = float(az_str)
            except ValueError:
                pass
        
        dip = -90.0
        dip_str = values.get(mappings.get("Dip", "Dip"), "")
        if dip_str:
            try:
                dip = float(dip_str)
            except ValueError:
                pass
        
        return CollarRecord(
            hole_id=hole_id,
            easting=easting,
            northing=northing,
            elevation=elevation,
            total_depth=total_depth,
            azimuth=azimuth,
            dip=dip,
            row_number=row_number
        )
    
    def _parse_survey_row(
        self,
        values: Dict[str, str],
        mappings: Dict[str, str],
        row_number: int
    ) -> Optional[SurveyRecord]:
        """Parse a single survey row."""
        hole_id = values.get(mappings.get("HoleID", "HoleID"), "").strip()
        if not hole_id:
            return None
        
        depth = float(values.get(mappings.get("Depth", "Depth"), 0))
        azimuth = float(values.get(mappings.get("Azimuth", "Azimuth"), 0))
        dip = float(values.get(mappings.get("Dip", "Dip"), -90))
        
        return SurveyRecord(
            hole_id=hole_id,
            depth=depth,
            azimuth=azimuth,
            dip=dip,
            row_number=row_number
        )
    
    def _parse_assay_row(
        self,
        values: Dict[str, str],
        mappings: Dict[str, str],
        quality_columns: List[str],
        row_number: int
    ) -> Optional[IntervalRecord]:
        """Parse a single assay row."""
        hole_id = values.get(mappings.get("HoleID", "HoleID"), "").strip()
        if not hole_id:
            return None
        
        from_depth = float(values.get(mappings.get("From", "From"), 0))
        to_depth = float(values.get(mappings.get("To", "To"), 0))
        
        seam_name = values.get(mappings.get("Seam", "Seam"), "").strip() or None
        lithology = values.get(mappings.get("Lithology", "Lithology"), "").strip() or None
        
        # Extract quality values
        quality_values = {}
        for col in quality_columns:
            val_str = values.get(col, "")
            if val_str:
                try:
                    quality_values[col] = float(val_str)
                except ValueError:
                    pass
        
        return IntervalRecord(
            hole_id=hole_id,
            from_depth=from_depth,
            to_depth=to_depth,
            seam_name=seam_name,
            lithology_code=lithology,
            quality_values=quality_values,
            row_number=row_number
        )
    
    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================
    
    def validate_records(
        self,
        collars: List[CollarRecord],
        surveys: List[SurveyRecord],
        intervals: List[IntervalRecord]
    ) -> List[ImportValidationError]:
        """
        Validate relationships between collar, survey, and interval data.
        """
        errors = []
        
        # Build lookup of collar IDs
        collar_ids = {c.hole_id for c in collars}
        collar_depths = {c.hole_id: c.total_depth for c in collars}
        
        # Validate surveys reference existing collars
        for survey in surveys:
            if survey.hole_id not in collar_ids:
                errors.append(ImportValidationError(
                    hole_id=survey.hole_id,
                    field="HoleID",
                    message=f"Survey references unknown hole ID",
                    row_number=survey.row_number,
                    severity="error"
                ))
            else:
                # Check survey depth doesn't exceed total depth
                total = collar_depths.get(survey.hole_id)
                if total and survey.depth > total:
                    errors.append(ImportValidationError(
                        hole_id=survey.hole_id,
                        field="Depth",
                        message=f"Survey depth {survey.depth}m exceeds total depth {total}m",
                        row_number=survey.row_number,
                        severity="warning"
                    ))
        
        # Validate intervals reference existing collars
        for interval in intervals:
            if interval.hole_id not in collar_ids:
                errors.append(ImportValidationError(
                    hole_id=interval.hole_id,
                    field="HoleID",
                    message=f"Interval references unknown hole ID",
                    row_number=interval.row_number,
                    severity="error"
                ))
            else:
                # Check interval doesn't exceed total depth
                total = collar_depths.get(interval.hole_id)
                if total and interval.to_depth > total:
                    errors.append(ImportValidationError(
                        hole_id=interval.hole_id,
                        field="To",
                        message=f"Interval to-depth {interval.to_depth}m exceeds total depth {total}m",
                        row_number=interval.row_number,
                        severity="warning"
                    ))
                
                # Check from < to
                if interval.from_depth >= interval.to_depth:
                    errors.append(ImportValidationError(
                        hole_id=interval.hole_id,
                        field="From/To",
                        message=f"From depth {interval.from_depth}m >= To depth {interval.to_depth}m",
                        row_number=interval.row_number,
                        severity="error"
                    ))
        
        return errors
    
    # =========================================================================
    # 3D TRACE CALCULATION
    # =========================================================================
    
    def calculate_3d_trace(
        self,
        collar: CollarRecord,
        surveys: List[SurveyRecord],
        interval_meters: float = 5.0
    ) -> List[Tuple[float, float, float, float]]:
        """
        Calculate 3D trace points for a borehole.
        
        Uses minimum curvature method for deviation calculations.
        
        Args:
            collar: Collar record with starting location
            surveys: Survey records sorted by depth
            interval_meters: Spacing between calculated points
            
        Returns:
            List of (depth, easting, northing, elevation) tuples
        """
        trace_points = []
        
        # Start at collar
        current_e = collar.easting
        current_n = collar.northing
        current_z = collar.elevation
        current_depth = 0.0
        
        trace_points.append((0.0, current_e, current_n, current_z))
        
        # Sort surveys by depth
        sorted_surveys = sorted(surveys, key=lambda s: s.depth)
        
        # Add collar as first "survey" if not present
        if not sorted_surveys or sorted_surveys[0].depth > 0:
            sorted_surveys.insert(0, SurveyRecord(
                hole_id=collar.hole_id,
                depth=0.0,
                azimuth=collar.azimuth,
                dip=collar.dip
            ))
        
        # Calculate trace between survey points
        for i in range(len(sorted_surveys) - 1):
            s1 = sorted_surveys[i]
            s2 = sorted_surveys[i + 1]
            
            # Minimum curvature calculation
            dMD = s2.depth - s1.depth  # Measured depth difference
            
            if dMD <= 0:
                continue
            
            # Convert angles to radians
            I1 = math.radians(90 + s1.dip)  # Inclination from vertical
            I2 = math.radians(90 + s2.dip)
            A1 = math.radians(s1.azimuth)
            A2 = math.radians(s2.azimuth)
            
            # Dogleg angle
            cos_DL = math.cos(I2 - I1) - math.sin(I1) * math.sin(I2) * (1 - math.cos(A2 - A1))
            cos_DL = max(-1, min(1, cos_DL))  # Clamp to valid range
            DL = math.acos(cos_DL)
            
            # Ratio factor
            if DL > 0.0001:
                RF = 2 / DL * math.tan(DL / 2)
            else:
                RF = 1.0
            
            # Displacements
            dN = (dMD / 2) * (math.sin(I1) * math.cos(A1) + math.sin(I2) * math.cos(A2)) * RF
            dE = (dMD / 2) * (math.sin(I1) * math.sin(A1) + math.sin(I2) * math.sin(A2)) * RF
            dZ = (dMD / 2) * (math.cos(I1) + math.cos(I2)) * RF
            
            # Update position
            current_e += dE
            current_n += dN
            current_z -= dZ  # Subtract because depth increases downward
            current_depth = s2.depth
            
            trace_points.append((current_depth, current_e, current_n, current_z))
        
        return trace_points
    
    # =========================================================================
    # IMPORT METHODS
    # =========================================================================
    
    def import_boreholes(
        self,
        site_id: str,
        collar_content: bytes,
        collar_filename: str,
        survey_content: Optional[bytes] = None,
        survey_filename: Optional[str] = None,
        assay_content: Optional[bytes] = None,
        assay_filename: Optional[str] = None,
        collar_mappings: Optional[Dict[str, str]] = None,
        survey_mappings: Optional[Dict[str, str]] = None,
        assay_mappings: Optional[Dict[str, str]] = None,
        quality_columns: Optional[List[str]] = None,
        source_format: str = "CSV"
    ) -> BoreholeImportResult:
        """
        Import borehole data from files.
        
        Args:
            site_id: Target site ID
            collar_content: Collar file content
            collar_filename: Collar filename
            survey_content: Optional survey file content
            assay_content: Optional assay file content
            *_mappings: Optional column mappings
            quality_columns: List of quality column names
            source_format: Source format identifier
            
        Returns:
            BoreholeImportResult with counts and errors
        """
        result = BoreholeImportResult(success=False)
        
        # Parse collars
        collars, collar_errors = self.parse_collar_file(
            collar_content, collar_filename, collar_mappings
        )
        result.errors.extend([e for e in collar_errors if e.severity == "error"])
        result.warnings.extend([e for e in collar_errors if e.severity == "warning"])
        
        if not collars:
            result.errors.append(ImportValidationError(
                hole_id="",
                field="",
                message="No valid collar records found"
            ))
            return result
        
        # Parse surveys
        surveys: List[SurveyRecord] = []
        if survey_content:
            surveys, survey_errors = self.parse_survey_file(
                survey_content, survey_filename or "survey.csv", survey_mappings
            )
            result.errors.extend([e for e in survey_errors if e.severity == "error"])
            result.warnings.extend([e for e in survey_errors if e.severity == "warning"])
        
        # Parse intervals/assays
        intervals: List[IntervalRecord] = []
        if assay_content:
            intervals, interval_errors = self.parse_assay_file(
                assay_content, assay_filename or "assay.csv", 
                assay_mappings, quality_columns
            )
            result.errors.extend([e for e in interval_errors if e.severity == "error"])
            result.warnings.extend([e for e in interval_errors if e.severity == "warning"])
        
        # Validate relationships
        validation_errors = self.validate_records(collars, surveys, intervals)
        result.errors.extend([e for e in validation_errors if e.severity == "error"])
        result.warnings.extend([e for e in validation_errors if e.severity == "warning"])
        
        # Check for blocking errors
        if any(e.severity == "error" for e in result.errors):
            return result
        
        # Create database records
        try:
            collar_map = self._create_collar_records(
                site_id, collars, source_format, collar_filename
            )
            result.collars_imported = len(collar_map)
            result.collar_ids = list(collar_map.values())
            
            # Create surveys
            if surveys:
                self._create_survey_records(collar_map, surveys)
                result.surveys_imported = len(surveys)
            
            # Calculate 3D traces
            surveys_by_hole = {}
            for s in surveys:
                if s.hole_id not in surveys_by_hole:
                    surveys_by_hole[s.hole_id] = []
                surveys_by_hole[s.hole_id].append(s)
            
            for collar in collars:
                hole_surveys = surveys_by_hole.get(collar.hole_id, [])
                trace_points = self.calculate_3d_trace(collar, hole_surveys)
                self._create_trace_records(collar_map[collar.hole_id], trace_points)
                result.traces_calculated += len(trace_points)
            
            # Create intervals and assays
            if intervals:
                interval_ids = self._create_interval_records(collar_map, intervals)
                result.intervals_imported = len(intervals)
                result.assays_imported = sum(
                    len(i.quality_values) for i in intervals
                )
            
            self.db.commit()
            result.success = True
            
        except Exception as e:
            self.db.rollback()
            result.errors.append(ImportValidationError(
                hole_id="",
                field="",
                message=f"Database error: {str(e)}"
            ))
        
        return result
    
    def _create_collar_records(
        self,
        site_id: str,
        collars: List[CollarRecord],
        source_format: str,
        source_file: str
    ) -> Dict[str, str]:
        """Create collar records and return hole_id -> collar_id map."""
        collar_map = {}
        
        for record in collars:
            collar = BoreholeCollar(
                site_id=site_id,
                hole_id=record.hole_id,
                easting=record.easting,
                northing=record.northing,
                elevation=record.elevation,
                total_depth=record.total_depth,
                azimuth=record.azimuth,
                dip=record.dip,
                hole_type=record.hole_type,
                source_format=source_format,
                source_file=source_file
            )
            self.db.add(collar)
            collar_map[record.hole_id] = collar.collar_id
        
        self.db.flush()  # Get IDs without committing
        return collar_map
    
    def _create_survey_records(
        self,
        collar_map: Dict[str, str],
        surveys: List[SurveyRecord]
    ):
        """Create survey records."""
        for record in surveys:
            if record.hole_id not in collar_map:
                continue
            
            survey = BoreholeSurvey(
                collar_id=collar_map[record.hole_id],
                depth=record.depth,
                azimuth=record.azimuth,
                dip=record.dip
            )
            self.db.add(survey)
    
    def _create_trace_records(
        self,
        collar_id: str,
        trace_points: List[Tuple[float, float, float, float]]
    ):
        """Create 3D trace records."""
        for i, (depth, e, n, z) in enumerate(trace_points):
            trace = Borehole3DTrace(
                collar_id=collar_id,
                sequence=i,
                depth=depth,
                easting=e,
                northing=n,
                elevation=z
            )
            self.db.add(trace)
    
    def _create_interval_records(
        self,
        collar_map: Dict[str, str],
        intervals: List[IntervalRecord]
    ) -> Dict[str, str]:
        """Create interval and assay records."""
        interval_map = {}
        
        for record in intervals:
            if record.hole_id not in collar_map:
                continue
            
            interval = BoreholeInterval(
                collar_id=collar_map[record.hole_id],
                from_depth=record.from_depth,
                to_depth=record.to_depth,
                seam_name=record.seam_name,
                lithology_code=record.lithology_code,
                quality_vector=record.quality_values
            )
            self.db.add(interval)
            self.db.flush()
            
            # Create individual assay records
            for field_name, value in record.quality_values.items():
                assay = BoreholeAssay(
                    interval_id=interval.interval_id,
                    quality_field_name=field_name,
                    value=value
                )
                self.db.add(assay)
            
            interval_map[f"{record.hole_id}_{record.from_depth}_{record.to_depth}"] = interval.interval_id
        
        return interval_map


def get_borehole_import_service(db: Session) -> BoreholeImportService:
    """Get a borehole import service instance."""
    return BoreholeImportService(db)
