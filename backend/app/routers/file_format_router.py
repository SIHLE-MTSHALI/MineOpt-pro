"""
File Format Router - Phase 1 File Format Foundation

REST API endpoints for file parsing, preview, and export.
Supports DXF, Surpac .str, CSV, and ASCII formats.

Endpoints:
- POST /files/parse - Parse uploaded file
- POST /files/preview - Preview first N rows
- POST /files/export - Export data to file format
- GET /files/formats - List supported formats
- GET /files/templates/{format} - Get import template
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
import io

from ..services.dxf_service import get_dxf_service, DXFParseResult, DXFExportConfig, DXFPoint
from ..services.surpac_parser import get_surpac_parser, SurpacParseResult, SurpacString
from ..services.tabular_parser import (
    get_tabular_parser, 
    TabularParseResult, 
    Delimiter,
    ColumnInfo,
    ImportTemplate,
    BoreholeBoreholePurpose
)


router = APIRouter(prefix="/files", tags=["File Formats"])


class FileFormat(str, Enum):
    """Supported file formats."""
    DXF = "dxf"
    SURPAC_STR = "str"
    CSV = "csv"
    TXT = "txt"
    ASCII = "ascii"


class ParseRequest(BaseModel):
    """Request parameters for file parsing."""
    delimiter: Optional[str] = None  # For CSV/TXT, None = auto-detect
    has_header: bool = True
    encoding: str = "utf-8"


class PreviewRequest(BaseModel):
    """Request parameters for file preview."""
    max_rows: int = Field(default=10, ge=1, le=100)
    delimiter: Optional[str] = None
    has_header: bool = True


class ExportFormat(str, Enum):
    """Export format options."""
    DXF = "dxf"
    SURPAC_STR = "str"
    CSV = "csv"


class ExportRequest(BaseModel):
    """Request for exporting data."""
    format: ExportFormat
    data: List[Dict[str, Any]]
    filename: str = "export"
    options: Dict[str, Any] = Field(default_factory=dict)


# Response Models

class FormatInfo(BaseModel):
    """Information about a supported format."""
    format: str
    name: str
    extensions: List[str]
    description: str
    supports_read: bool
    supports_write: bool


class DXFEntityResponse(BaseModel):
    """DXF entity in response."""
    entity_type: str
    layer: str
    point_count: int
    is_closed: bool


class DXFParseResponse(BaseModel):
    """Response from parsing a DXF file."""
    success: bool
    filename: Optional[str]
    version: Optional[str]
    layers: List[str]
    entity_count: int
    point_count: int
    polyline_count: int
    face_count: int
    extent_min: Optional[List[float]]
    extent_max: Optional[List[float]]
    entities: List[DXFEntityResponse]
    errors: List[str]
    warnings: List[str]


class SurpacStringResponse(BaseModel):
    """Surpac string in response."""
    string_number: int
    point_count: int
    is_closed: bool
    first_descriptor: Optional[str]


class SurpacParseResponse(BaseModel):
    """Response from parsing a Surpac file."""
    success: bool
    filename: Optional[str]
    string_count: int
    point_count: int
    descriptor_count: int
    extent_min: Optional[List[float]]
    extent_max: Optional[List[float]]
    strings: List[SurpacStringResponse]
    errors: List[str]
    warnings: List[str]


class ColumnInfoResponse(BaseModel):
    """Column info in response."""
    index: int
    name: str
    inferred_type: str
    sample_values: List[str]
    null_count: int
    unique_count: int
    suggested_mapping: Optional[str]


class TabularParseResponse(BaseModel):
    """Response from parsing a tabular file."""
    success: bool
    filename: Optional[str]
    delimiter: str
    has_header: bool
    row_count: int
    column_count: int
    inferred_purpose: str
    columns: List[ColumnInfoResponse]
    preview_rows: List[Dict[str, str]]
    errors: List[str]
    warnings: List[str]


class TemplateResponse(BaseModel):
    """Import template response."""
    name: str
    purpose: str
    required_columns: List[str]
    optional_columns: List[str]
    column_mappings: Dict[str, str]
    description: str


# Endpoints

@router.get("/formats", response_model=List[FormatInfo])
async def list_formats():
    """List all supported file formats."""
    return [
        FormatInfo(
            format="dxf",
            name="AutoCAD DXF",
            extensions=[".dxf"],
            description="Drawing Interchange Format for CAD geometry",
            supports_read=True,
            supports_write=True
        ),
        FormatInfo(
            format="str",
            name="Surpac String",
            extensions=[".str"],
            description="GEOVIA Surpac 3D string file (ASCII)",
            supports_read=True,
            supports_write=True
        ),
        FormatInfo(
            format="csv",
            name="CSV",
            extensions=[".csv"],
            description="Comma-separated values (Vulcan, Minex, GeoBank exports)",
            supports_read=True,
            supports_write=True
        ),
        FormatInfo(
            format="txt",
            name="Text/ASCII",
            extensions=[".txt", ".dat", ".asc"],
            description="Delimited text files (tab, space, semicolon)",
            supports_read=True,
            supports_write=True
        ),
    ]


@router.post("/parse/dxf", response_model=DXFParseResponse)
async def parse_dxf(file: UploadFile = File(...)):
    """
    Parse a DXF file and extract geometry.
    
    Returns layers, entities, and extents.
    """
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(400, "File must have .dxf extension")
    
    content = await file.read()
    
    try:
        service = get_dxf_service()
        result = service.parse_bytes(content, file.filename)
        
        # Convert to response format
        entities = [
            DXFEntityResponse(
                entity_type=e.entity_type.value,
                layer=e.layer,
                point_count=len(e.points),
                is_closed=e.is_closed
            )
            for e in result.entities[:100]  # Limit to first 100 for response
        ]
        
        return DXFParseResponse(
            success=result.success,
            filename=result.filename,
            version=result.version,
            layers=result.layers,
            entity_count=result.entity_count,
            point_count=result.point_count,
            polyline_count=result.polyline_count,
            face_count=result.face_count,
            extent_min=[result.extent_min.x, result.extent_min.y, result.extent_min.z] if result.extent_min else None,
            extent_max=[result.extent_max.x, result.extent_max.y, result.extent_max.z] if result.extent_max else None,
            entities=entities,
            errors=result.errors,
            warnings=result.warnings
        )
    except ImportError as e:
        raise HTTPException(500, f"DXF parsing unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Failed to parse DXF: {str(e)}")


@router.post("/parse/surpac", response_model=SurpacParseResponse)
async def parse_surpac(file: UploadFile = File(...)):
    """
    Parse a Surpac .str file.
    
    Returns strings, points, and extents.
    """
    if not file.filename.lower().endswith('.str'):
        raise HTTPException(400, "File must have .str extension")
    
    content = await file.read()
    
    try:
        parser = get_surpac_parser()
        result = parser.parse_bytes(content, file.filename)
        
        # Convert to response format
        strings = [
            SurpacStringResponse(
                string_number=s.string_number,
                point_count=s.point_count,
                is_closed=s.is_closed,
                first_descriptor=s.get_first_descriptor(0)
            )
            for s in result.strings[:100]  # Limit for response
        ]
        
        return SurpacParseResponse(
            success=result.success,
            filename=result.filename,
            string_count=result.string_count,
            point_count=result.point_count,
            descriptor_count=result.descriptor_count,
            extent_min=list(result.extent_min) if result.extent_min else None,
            extent_max=list(result.extent_max) if result.extent_max else None,
            strings=strings,
            errors=result.errors,
            warnings=result.warnings
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to parse Surpac file: {str(e)}")


@router.post("/parse/tabular", response_model=TabularParseResponse)
async def parse_tabular(
    file: UploadFile = File(...),
    delimiter: Optional[str] = Query(None, description="Delimiter (comma, tab, etc). Auto-detect if not specified."),
    has_header: bool = Query(True, description="Whether file has header row")
):
    """
    Parse a CSV or delimited text file.
    
    Supports auto-detection of delimiter and column types.
    Returns column info and data preview.
    """
    content = await file.read()
    
    try:
        parser = get_tabular_parser()
        
        # Determine delimiter
        delim = Delimiter.AUTO
        if delimiter:
            if delimiter == "comma" or delimiter == ",":
                delim = Delimiter.COMMA
            elif delimiter == "tab" or delimiter == "\t":
                delim = Delimiter.TAB
            elif delimiter == "semicolon" or delimiter == ";":
                delim = Delimiter.SEMICOLON
            elif delimiter == "space" or delimiter == " ":
                delim = Delimiter.SPACE
        
        result = parser.parse_bytes(content, file.filename, delim, has_header)
        
        # Build column info response
        columns = [
            ColumnInfoResponse(
                index=c.index,
                name=c.name,
                inferred_type=c.inferred_type.value,
                sample_values=c.sample_values[:5],
                null_count=c.null_count,
                unique_count=c.unique_count,
                suggested_mapping=c.suggested_mapping
            )
            for c in result.columns
        ]
        
        # Preview rows (first 10)
        preview = [row.values for row in result.rows[:10]]
        
        return TabularParseResponse(
            success=result.success,
            filename=result.filename,
            delimiter=result.delimiter,
            has_header=result.has_header,
            row_count=result.row_count,
            column_count=result.column_count,
            inferred_purpose=result.inferred_purpose.value,
            columns=columns,
            preview_rows=preview,
            errors=result.errors,
            warnings=result.warnings
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to parse file: {str(e)}")


@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates():
    """List available import templates."""
    parser = get_tabular_parser()
    templates = []
    
    for key in parser.list_templates():
        t = parser.get_template(key)
        if t:
            templates.append(TemplateResponse(
                name=t.name,
                purpose=t.purpose.value,
                required_columns=t.required_columns,
                optional_columns=t.optional_columns,
                column_mappings=t.column_mappings,
                description=t.description
            ))
    
    return templates


@router.get("/templates/{template_key}", response_model=TemplateResponse)
async def get_template(template_key: str):
    """Get a specific import template."""
    parser = get_tabular_parser()
    t = parser.get_template(template_key)
    
    if not t:
        raise HTTPException(404, f"Template '{template_key}' not found")
    
    return TemplateResponse(
        name=t.name,
        purpose=t.purpose.value,
        required_columns=t.required_columns,
        optional_columns=t.optional_columns,
        column_mappings=t.column_mappings,
        description=t.description
    )


@router.post("/export/dxf")
async def export_dxf(request: ExportRequest):
    """
    Export data to DXF format.
    
    Expects data with geometry (vertices) for each item.
    """
    try:
        service = get_dxf_service()
        
        # Export as activity areas
        dxf_bytes = service.export_activity_areas(
            request.data,
            file_path=None,
            config=DXFExportConfig(**request.options) if request.options else None
        )
        
        return StreamingResponse(
            io.BytesIO(dxf_bytes),
            media_type="application/dxf",
            headers={"Content-Disposition": f"attachment; filename={request.filename}.dxf"}
        )
    except ImportError as e:
        raise HTTPException(500, f"DXF export unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.post("/export/surpac")
async def export_surpac(request: ExportRequest):
    """
    Export data to Surpac .str format.
    
    Expects data with geometry (vertices) for each item.
    """
    try:
        parser = get_surpac_parser()
        
        # Convert data to SurpacStrings
        strings = []
        for i, item in enumerate(request.data, start=1):
            geometry = item.get("geometry", {})
            surpac_string = parser.from_activity_area_geometry(
                geometry,
                string_number=i,
                descriptor=item.get("name", "")
            )
            strings.append(surpac_string)
        
        # Export
        content_bytes = parser.export_to_bytes(
            strings,
            header_purpose=request.options.get("purpose", "Exported from MineOpt Pro"),
            location_code=request.options.get("location_code", "MINEOPT")
        )
        
        return StreamingResponse(
            io.BytesIO(content_bytes),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={request.filename}.str"}
        )
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.post("/export/csv")
async def export_csv(request: ExportRequest):
    """
    Export data to CSV format.
    """
    try:
        parser = get_tabular_parser()
        
        columns = request.options.get("columns")
        content = parser.export_to_csv(request.data, columns)
        
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={request.filename}.csv"}
        )
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")
