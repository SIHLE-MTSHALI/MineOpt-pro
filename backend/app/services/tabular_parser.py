"""
Tabular Data Parser - Phase 1 File Format Foundation

Generic parser for tabular data files (CSV, TXT, ASCII).
Supports multiple mining software export formats:
- Vulcan (CSV with collar/survey/assay files)
- Minex (CSV with format file concepts)
- GeoBank (CSV/TXT exports)
- Generic delimited files

Features:
- Auto-detect delimiter (comma, tab, semicolon, space)
- Column type inference
- Header row detection
- Configurable column mapping
- Format templates for common structures
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union, Tuple
from enum import Enum
import csv
import io
import re


class Delimiter(str, Enum):
    """Supported file delimiters."""
    COMMA = ","
    TAB = "\t"
    SEMICOLON = ";"
    SPACE = " "
    PIPE = "|"
    AUTO = "auto"


class ColumnType(str, Enum):
    """Inferred column data types."""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    DATE = "date"
    BOOLEAN = "boolean"
    EMPTY = "empty"


class BoreholeBoreholePurpose(str, Enum):
    """Purpose of borehole data file."""
    COLLAR = "collar"
    SURVEY = "survey"
    ASSAY = "assay"
    LITHOLOGY = "lithology"
    INTERVAL = "interval"
    UNKNOWN = "unknown"


@dataclass
class ColumnInfo:
    """Information about a column in the data."""
    index: int
    name: str
    inferred_type: ColumnType
    sample_values: List[Any] = field(default_factory=list)
    null_count: int = 0
    unique_count: int = 0
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    suggested_mapping: Optional[str] = None


@dataclass
class ParsedRow:
    """A parsed row of data."""
    row_number: int
    values: Dict[str, Any]
    raw_values: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class TabularParseResult:
    """Result of parsing a tabular data file."""
    success: bool
    filename: Optional[str] = None
    delimiter: str = ","
    has_header: bool = True
    columns: List[ColumnInfo] = field(default_factory=list)
    rows: List[ParsedRow] = field(default_factory=list)
    row_count: int = 0
    column_count: int = 0
    inferred_purpose: BoreholeBoreholePurpose = BoreholeBoreholePurpose.UNKNOWN
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ColumnMapping:
    """Maps a source column to a target field."""
    source_column: str
    target_field: str
    transform: Optional[str] = None  # e.g., "multiply:0.01" for percentage


@dataclass
class ImportTemplate:
    """Template for importing a specific file format."""
    name: str
    purpose: BoreholeBoreholePurpose
    required_columns: List[str]
    optional_columns: List[str] = field(default_factory=list)
    column_mappings: Dict[str, str] = field(default_factory=dict)  # alias -> standard
    description: str = ""


# Pre-defined import templates for common formats
IMPORT_TEMPLATES = {
    "vulcan_collar": ImportTemplate(
        name="Vulcan Collar",
        purpose=BoreholeBoreholePurpose.COLLAR,
        required_columns=["HoleID", "Easting", "Northing", "Elevation"],
        optional_columns=["TotalDepth", "Azimuth", "Dip", "Status"],
        column_mappings={
            "HOLE_ID": "HoleID",
            "HOLEID": "HoleID",
            "BHID": "HoleID",
            "HOLE": "HoleID",
            "EAST": "Easting",
            "X": "Easting",
            "NORTH": "Northing",
            "Y": "Northing",
            "ELEV": "Elevation",
            "RL": "Elevation",
            "Z": "Elevation",
            "COLLAR_RL": "Elevation",
            "DEPTH": "TotalDepth",
            "TOTAL_DEPTH": "TotalDepth",
            "MAX_DEPTH": "TotalDepth",
            "EOH": "TotalDepth",
        },
        description="Standard Vulcan drillhole collar format"
    ),
    "vulcan_survey": ImportTemplate(
        name="Vulcan Survey",
        purpose=BoreholeBoreholePurpose.SURVEY,
        required_columns=["HoleID", "Depth", "Azimuth", "Dip"],
        optional_columns=["SurveyMethod"],
        column_mappings={
            "HOLE_ID": "HoleID",
            "HOLEID": "HoleID",
            "BHID": "HoleID",
            "AT": "Depth",
            "SURVEY_DEPTH": "Depth",
            "BEARING": "Azimuth",
            "AZI": "Azimuth",
            "INCLINATION": "Dip",
            "DIP_ANGLE": "Dip",
        },
        description="Standard Vulcan downhole survey format"
    ),
    "vulcan_assay": ImportTemplate(
        name="Vulcan Assay",
        purpose=BoreholeBoreholePurpose.ASSAY,
        required_columns=["HoleID", "From", "To"],
        optional_columns=["SampleID", "Seam"],
        column_mappings={
            "HOLE_ID": "HoleID",
            "HOLEID": "HoleID",
            "BHID": "HoleID",
            "FROM_DEPTH": "From",
            "FROM_M": "From",
            "FROMDEPTH": "From",
            "TO_DEPTH": "To",
            "TO_M": "To",
            "TODEPTH": "To",
            "LENGTH": "Interval",
        },
        description="Standard Vulcan assay interval format"
    ),
    "minex_collar": ImportTemplate(
        name="Minex Collar",
        purpose=BoreholeBoreholePurpose.COLLAR,
        required_columns=["BH_NAME", "EAST", "NORTH", "COLLAR_RL"],
        optional_columns=["DEPTH", "AZIMUTH", "DIP", "TYPE"],
        column_mappings={
            "BH_NAME": "HoleID",
            "BHNAME": "HoleID",
            "EAST": "Easting",
            "NORTH": "Northing",
            "COLLAR_RL": "Elevation",
            "RL": "Elevation",
        },
        description="GEOVIA Minex borehole collar format"
    ),
    "generic_xyz": ImportTemplate(
        name="Generic XYZ",
        purpose=BoreholeBoreholePurpose.UNKNOWN,
        required_columns=["X", "Y", "Z"],
        optional_columns=["ID", "Name", "Description"],
        column_mappings={
            "EASTING": "X",
            "EAST": "X",
            "NORTHING": "Y",
            "NORTH": "Y",
            "ELEVATION": "Z",
            "RL": "Z",
            "HEIGHT": "Z",
        },
        description="Generic XYZ point data"
    ),
}


class TabularParser:
    """
    Generic parser for tabular data files.
    
    Provides:
    - Auto-detect delimiter and header
    - Column type inference
    - Template-based column mapping
    - Format-specific parsing for mining software exports
    """
    
    def __init__(self):
        self.templates = IMPORT_TEMPLATES.copy()
    
    def parse_file(
        self, 
        file_path: str,
        delimiter: Delimiter = Delimiter.AUTO,
        has_header: bool = True,
        encoding: str = "utf-8"
    ) -> TabularParseResult:
        """
        Parse a tabular data file.
        
        Args:
            file_path: Path to the file
            delimiter: Delimiter to use (or AUTO to detect)
            has_header: Whether file has a header row
            encoding: File encoding
            
        Returns:
            TabularParseResult with parsed data
        """
        result = TabularParseResult(success=False, filename=file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            
            self._parse_content(content, result, delimiter, has_header)
            result.success = len(result.errors) == 0
            
        except Exception as e:
            result.errors.append(f"Failed to read file: {str(e)}")
        
        return result
    
    def parse_string(
        self,
        content: str,
        filename: str = "data.csv",
        delimiter: Delimiter = Delimiter.AUTO,
        has_header: bool = True
    ) -> TabularParseResult:
        """Parse tabular data from a string."""
        result = TabularParseResult(success=False, filename=filename)
        
        try:
            self._parse_content(content, result, delimiter, has_header)
            result.success = len(result.errors) == 0
        except Exception as e:
            result.errors.append(f"Failed to parse content: {str(e)}")
        
        return result
    
    def parse_bytes(
        self,
        file_bytes: bytes,
        filename: str = "data.csv",
        delimiter: Delimiter = Delimiter.AUTO,
        has_header: bool = True,
        encoding: str = "utf-8"
    ) -> TabularParseResult:
        """Parse tabular data from bytes."""
        try:
            content = file_bytes.decode(encoding, errors='replace')
            return self.parse_string(content, filename, delimiter, has_header)
        except Exception as e:
            result = TabularParseResult(success=False, filename=filename)
            result.errors.append(f"Failed to decode file: {str(e)}")
            return result
    
    def _parse_content(
        self,
        content: str,
        result: TabularParseResult,
        delimiter: Delimiter,
        has_header: bool
    ):
        """Parse file content."""
        lines = content.strip().split('\n')
        
        if not lines:
            result.errors.append("File is empty")
            return
        
        # Detect delimiter
        if delimiter == Delimiter.AUTO:
            detected = self._detect_delimiter(lines[0])
            result.delimiter = detected
        else:
            result.delimiter = delimiter.value
        
        result.has_header = has_header
        
        # Parse with CSV reader
        reader = csv.reader(io.StringIO(content), delimiter=result.delimiter)
        all_rows = list(reader)
        
        if not all_rows:
            result.errors.append("No data rows found")
            return
        
        # Extract header
        if has_header:
            header_row = all_rows[0]
            data_rows = all_rows[1:]
        else:
            # Generate column names
            header_row = [f"Column_{i+1}" for i in range(len(all_rows[0]))]
            data_rows = all_rows
        
        result.column_count = len(header_row)
        
        # Create column info
        for i, name in enumerate(header_row):
            col_info = ColumnInfo(
                index=i,
                name=name.strip(),
                inferred_type=ColumnType.EMPTY
            )
            result.columns.append(col_info)
        
        # Parse data rows
        for row_num, row_data in enumerate(data_rows, start=1 if has_header else 0):
            parsed_row = ParsedRow(
                row_number=row_num,
                values={},
                raw_values=row_data
            )
            
            for i, value in enumerate(row_data):
                if i < len(result.columns):
                    col = result.columns[i]
                    cleaned_value = value.strip()
                    parsed_row.values[col.name] = cleaned_value
                    
                    # Add to sample values
                    if len(col.sample_values) < 10:
                        col.sample_values.append(cleaned_value)
                    
                    # Track nulls
                    if not cleaned_value:
                        col.null_count += 1
            
            result.rows.append(parsed_row)
        
        result.row_count = len(result.rows)
        
        # Infer column types
        self._infer_column_types(result)
        
        # Infer file purpose
        result.inferred_purpose = self._infer_purpose(result)
        
        # Suggest column mappings
        self._suggest_mappings(result)
    
    def _detect_delimiter(self, sample_line: str) -> str:
        """Auto-detect the delimiter from a sample line."""
        delimiters = [',', '\t', ';', '|', ' ']
        counts = {}
        
        for d in delimiters:
            counts[d] = sample_line.count(d)
        
        # Return delimiter with highest count
        best = max(counts, key=counts.get)
        
        # If no delimiter found with count > 0, default to comma
        if counts[best] == 0:
            return ','
        
        return best
    
    def _infer_column_types(self, result: TabularParseResult):
        """Infer data types for each column."""
        for col in result.columns:
            type_counts = {t: 0 for t in ColumnType}
            numeric_values = []
            
            for row in result.rows:
                value = row.values.get(col.name, "")
                if not value:
                    type_counts[ColumnType.EMPTY] += 1
                    continue
                
                # Try to parse as number
                try:
                    if '.' in value or 'e' in value.lower():
                        float_val = float(value)
                        type_counts[ColumnType.FLOAT] += 1
                        numeric_values.append(float_val)
                    else:
                        int_val = int(value)
                        type_counts[ColumnType.INTEGER] += 1
                        numeric_values.append(float(int_val))
                except ValueError:
                    # Check for date patterns
                    if re.match(r'\d{4}[-/]\d{2}[-/]\d{2}', value):
                        type_counts[ColumnType.DATE] += 1
                    elif value.lower() in ['true', 'false', 'yes', 'no', '1', '0']:
                        type_counts[ColumnType.BOOLEAN] += 1
                    else:
                        type_counts[ColumnType.STRING] += 1
            
            # Determine primary type (excluding EMPTY)
            non_empty = {k: v for k, v in type_counts.items() if k != ColumnType.EMPTY}
            if non_empty:
                col.inferred_type = max(non_empty, key=non_empty.get)
            else:
                col.inferred_type = ColumnType.EMPTY
            
            # Calculate min/max for numeric columns
            if numeric_values:
                col.min_value = min(numeric_values)
                col.max_value = max(numeric_values)
            
            # Count unique values
            unique = set(row.values.get(col.name, "") for row in result.rows)
            col.unique_count = len(unique)
    
    def _infer_purpose(self, result: TabularParseResult) -> BoreholeBoreholePurpose:
        """Infer the purpose of the file based on column names."""
        column_names_upper = [c.name.upper() for c in result.columns]
        
        # Check for collar indicators
        collar_indicators = ["HOLEID", "HOLE_ID", "BHID", "EASTING", "EAST", 
                           "NORTHING", "NORTH", "ELEVATION", "RL", "COLLAR"]
        collar_matches = sum(1 for ind in collar_indicators if any(ind in cn for cn in column_names_upper))
        
        # Check for survey indicators
        survey_indicators = ["DEPTH", "AZIMUTH", "AZI", "DIP", "INCLINATION", "SURVEY"]
        survey_matches = sum(1 for ind in survey_indicators if any(ind in cn for cn in column_names_upper))
        
        # Check for assay indicators
        assay_indicators = ["FROM", "TO", "SAMPLE", "ASH", "CV", "MOISTURE", "SULPHUR", "QUALITY"]
        assay_matches = sum(1 for ind in assay_indicators if any(ind in cn for cn in column_names_upper))
        
        # Check for lithology indicators
        lith_indicators = ["LITHOLOGY", "LITH", "ROCK", "GEOLOGY", "FORMATION"]
        lith_matches = sum(1 for ind in lith_indicators if any(ind in cn for cn in column_names_upper))
        
        # Determine purpose based on matches
        scores = {
            BoreholeBoreholePurpose.COLLAR: collar_matches,
            BoreholeBoreholePurpose.SURVEY: survey_matches,
            BoreholeBoreholePurpose.ASSAY: assay_matches,
            BoreholeBoreholePurpose.LITHOLOGY: lith_matches,
        }
        
        best = max(scores, key=scores.get)
        if scores[best] >= 2:
            return best
        
        return BoreholeBoreholePurpose.UNKNOWN
    
    def _suggest_mappings(self, result: TabularParseResult):
        """Suggest column mappings based on templates."""
        # Find matching template
        template = None
        for t in self.templates.values():
            if t.purpose == result.inferred_purpose:
                template = t
                break
        
        if not template:
            return
        
        # Map columns using template
        for col in result.columns:
            col_upper = col.name.upper().strip()
            
            # Check direct match
            if col_upper in template.column_mappings:
                col.suggested_mapping = template.column_mappings[col_upper]
            elif col.name in template.required_columns:
                col.suggested_mapping = col.name
            elif col.name in template.optional_columns:
                col.suggested_mapping = col.name
            else:
                # Check partial matches
                for alias, target in template.column_mappings.items():
                    if alias in col_upper or col_upper in alias:
                        col.suggested_mapping = target
                        break
    
    # =========================================================================
    # CONVERSION FUNCTIONS
    # =========================================================================
    
    def apply_mapping(
        self,
        result: TabularParseResult,
        mappings: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Apply column mappings to create standardized output.
        
        Args:
            result: Parsed result
            mappings: Dict of source_column -> target_field
            
        Returns:
            List of dicts with mapped field names
        """
        output = []
        
        for row in result.rows:
            mapped_row = {}
            for source, target in mappings.items():
                if source in row.values:
                    value = row.values[source]
                    # Try to convert to appropriate type
                    for col in result.columns:
                        if col.name == source:
                            if col.inferred_type == ColumnType.FLOAT:
                                try:
                                    value = float(value) if value else None
                                except ValueError:
                                    pass
                            elif col.inferred_type == ColumnType.INTEGER:
                                try:
                                    value = int(float(value)) if value else None
                                except ValueError:
                                    pass
                            break
                    mapped_row[target] = value
            output.append(mapped_row)
        
        return output
    
    def to_borehole_collars(
        self,
        result: TabularParseResult,
        mappings: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Convert parsed data to borehole collar records.
        
        Uses suggested mappings if none provided.
        """
        if mappings is None:
            mappings = {
                c.name: c.suggested_mapping 
                for c in result.columns 
                if c.suggested_mapping
            }
        
        return self.apply_mapping(result, mappings)
    
    def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> str:
        """
        Export data to CSV format.
        
        Args:
            data: List of dicts to export
            columns: Column order (if None, uses keys from first row)
            
        Returns:
            CSV content as string
        """
        if not data:
            return ""
        
        if columns is None:
            columns = list(data[0].keys())
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    def add_template(self, key: str, template: ImportTemplate):
        """Add a custom import template."""
        self.templates[key] = template
    
    def get_template(self, key: str) -> Optional[ImportTemplate]:
        """Get an import template by key."""
        return self.templates.get(key)
    
    def list_templates(self) -> List[str]:
        """List available template keys."""
        return list(self.templates.keys())


# Singleton instance
_tabular_parser: Optional[TabularParser] = None


def get_tabular_parser() -> TabularParser:
    """Get the singleton tabular parser instance."""
    global _tabular_parser
    if _tabular_parser is None:
        _tabular_parser = TabularParser()
    return _tabular_parser
