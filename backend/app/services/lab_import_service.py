"""
Lab Results Import Service

Handles import of laboratory quality analysis results with:
- Delayed data handling (samples taken earlier, results arrive later)
- Sample-to-parcel/period matching
- Revision of previously imported results
- Quality recalculation triggers
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid


class ImportStatus(Enum):
    PENDING = "pending"
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    REVISED = "revised"
    ERROR = "error"


@dataclass
class LabSample:
    """Represents a single lab sample result."""
    sample_id: str
    sample_date: datetime
    result_date: datetime
    source_location: str  # External ID for source (pit, block, etc.)
    quality_values: Dict[str, float]  # {field: value}
    sample_type: str = "routine"  # routine, check, duplicate
    external_ref: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ImportResult:
    """Result of a lab import operation."""
    import_id: str
    timestamp: datetime
    total_records: int
    matched: int
    unmatched: int
    revised: int
    errors: int
    details: List[Dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class LabResultsImportService:
    """
    Service for importing lab results and matching to schedule data.
    
    Supports delayed data - samples may arrive hours or days after
    the material was actually processed, requiring retroactive matching.
    """

    def __init__(self, db=None):
        self.db = db
        self._id_mappings: Dict[str, str] = {}  # external_id -> internal_id
        self._pending_samples: List[LabSample] = []

    def set_id_mapping(self, external_id: str, internal_id: str, entity_type: str = "parcel"):
        """
        Register mapping between external system ID and internal ID.
        
        Args:
            external_id: ID from external system (lab, fleet, etc.)
            internal_id: Internal MineOpt ID
            entity_type: Type of entity (parcel, period, resource)
        """
        key = f"{entity_type}:{external_id}"
        self._id_mappings[key] = internal_id

    def get_internal_id(self, external_id: str, entity_type: str = "parcel") -> Optional[str]:
        """Lookup internal ID from external ID."""
        key = f"{entity_type}:{external_id}"
        return self._id_mappings.get(key)

    def import_lab_results(
        self,
        records: List[Dict],
        handle_delayed: bool = True,
        auto_match: bool = True,
        revision_mode: str = "update"  # update, append, reject
    ) -> ImportResult:
        """
        Import laboratory results from external source.
        
        Args:
            records: List of lab result records
            handle_delayed: Whether to handle delayed data matching
            auto_match: Whether to auto-match by location/date
            revision_mode: How to handle revised results
            
        Returns:
            ImportResult with matching statistics
        """
        import_id = f"import-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        matched = 0
        unmatched = 0
        revised = 0
        errors = 0
        details = []
        warnings = []

        for record in records:
            try:
                sample = self._parse_record(record)
                match_result = self._match_sample(sample, auto_match, handle_delayed)
                
                if match_result["status"] == ImportStatus.MATCHED:
                    # Apply quality values
                    self._apply_sample(sample, match_result["target_id"], revision_mode)
                    matched += 1
                    details.append({
                        "sample_id": sample.sample_id,
                        "status": "matched",
                        "target_id": match_result["target_id"],
                        "match_type": match_result.get("match_type", "direct")
                    })
                elif match_result["status"] == ImportStatus.REVISED:
                    self._apply_revision(sample, match_result["target_id"])
                    revised += 1
                    details.append({
                        "sample_id": sample.sample_id,
                        "status": "revised",
                        "target_id": match_result["target_id"],
                        "previous_values": match_result.get("previous_values", {})
                    })
                else:
                    # Could not match - add to pending
                    if handle_delayed:
                        self._pending_samples.append(sample)
                    unmatched += 1
                    details.append({
                        "sample_id": sample.sample_id,
                        "status": "unmatched",
                        "reason": match_result.get("reason", "No matching target found")
                    })
                    
            except Exception as e:
                errors += 1
                details.append({
                    "record": record,
                    "status": "error",
                    "error": str(e)
                })

        # Check if unmatched rate is high
        if records and (unmatched / len(records)) > 0.2:
            warnings.append(f"High unmatched rate: {unmatched}/{len(records)} records couldn't be matched")

        return ImportResult(
            import_id=import_id,
            timestamp=datetime.utcnow(),
            total_records=len(records),
            matched=matched,
            unmatched=unmatched,
            revised=revised,
            errors=errors,
            details=details,
            warnings=warnings
        )

    def _parse_record(self, record: Dict) -> LabSample:
        """Parse a raw record into a LabSample."""
        return LabSample(
            sample_id=record.get("sample_id", f"sample-{uuid.uuid4().hex[:8]}"),
            sample_date=self._parse_date(record.get("sample_date")),
            result_date=self._parse_date(record.get("result_date", datetime.utcnow())),
            source_location=record.get("source_location", record.get("location", "")),
            quality_values=record.get("quality_values", record.get("quality", {})),
            sample_type=record.get("sample_type", "routine"),
            external_ref=record.get("external_ref"),
            notes=record.get("notes")
        )

    def _parse_date(self, value) -> datetime:
        """Parse date from various formats."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            # Try common formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return datetime.utcnow()

    def _match_sample(
        self,
        sample: LabSample,
        auto_match: bool,
        handle_delayed: bool
    ) -> Dict[str, Any]:
        """
        Match a sample to a parcel or period.
        
        Matching strategies:
        1. Direct ID mapping (if external_ref mapped)
        2. Location + date window match
        3. Fuzzy location matching with date
        """
        # Try direct mapping first
        if sample.external_ref:
            internal_id = self.get_internal_id(sample.external_ref, "parcel")
            if internal_id:
                return {
                    "status": ImportStatus.MATCHED,
                    "target_id": internal_id,
                    "match_type": "direct_mapping"
                }

        # Try location mapping
        if sample.source_location:
            internal_id = self.get_internal_id(sample.source_location, "parcel")
            if internal_id:
                return {
                    "status": ImportStatus.MATCHED,
                    "target_id": internal_id,
                    "match_type": "location_mapping"
                }

        if not auto_match:
            return {
                "status": ImportStatus.UNMATCHED,
                "reason": "Auto-matching disabled"
            }

        # Auto-match by location and date (would query DB in production)
        # For now, return unmatched - in production this would do fuzzy matching
        return {
            "status": ImportStatus.UNMATCHED,
            "reason": "No matching parcel found for location and date"
        }

    def _apply_sample(self, sample: LabSample, target_id: str, revision_mode: str):
        """Apply sample quality values to matched target."""
        # In production, would update database
        # For now, just log
        print(f"Applying sample {sample.sample_id} to target {target_id}")
        print(f"  Quality: {sample.quality_values}")

    def _apply_revision(self, sample: LabSample, target_id: str):
        """Apply revised sample values."""
        print(f"Revising sample {sample.sample_id} for target {target_id}")

    def process_pending_samples(self) -> int:
        """
        Retry matching for pending samples.
        Called periodically or when new data arrives.
        
        Returns:
            Number of newly matched samples
        """
        matched_count = 0
        still_pending = []

        for sample in self._pending_samples:
            # Check if sample is too old (e.g., > 7 days)
            age = datetime.utcnow() - sample.sample_date
            if age > timedelta(days=7):
                continue  # Drop old unmatched samples

            # Retry matching
            match_result = self._match_sample(sample, auto_match=True, handle_delayed=True)
            if match_result["status"] == ImportStatus.MATCHED:
                self._apply_sample(sample, match_result["target_id"], "update")
                matched_count += 1
            else:
                still_pending.append(sample)

        self._pending_samples = still_pending
        return matched_count

    def get_pending_count(self) -> int:
        """Get count of pending unmatched samples."""
        return len(self._pending_samples)

    def export_unmatched(self) -> List[Dict]:
        """Export unmatched samples for manual review."""
        return [
            {
                "sample_id": s.sample_id,
                "sample_date": s.sample_date.isoformat(),
                "source_location": s.source_location,
                "quality_values": s.quality_values,
                "sample_type": s.sample_type
            }
            for s in self._pending_samples
        ]


# BI Extract Publishing
class BIExtractService:
    """
    Service for publishing data extracts to BI systems.
    
    Supports:
    - Scheduled extract generation
    - Multiple output formats (JSON, CSV, Parquet)
    - Push to data warehouse endpoints
    """

    def __init__(self, db=None):
        self.db = db
        self._extract_configs: Dict[str, Dict] = {}

    def register_extract(
        self,
        extract_id: str,
        name: str,
        query_type: str,  # schedule, actuals, quality, stockpile
        output_format: str = "json",
        destination: Optional[str] = None,  # URL or file path
        schedule_cron: Optional[str] = None  # Cron expression for scheduling
    ):
        """Register a BI extract configuration."""
        self._extract_configs[extract_id] = {
            "name": name,
            "query_type": query_type,
            "output_format": output_format,
            "destination": destination,
            "schedule_cron": schedule_cron,
            "last_run": None
        }

    def generate_extract(self, extract_id: str, params: Optional[Dict] = None) -> Dict:
        """
        Generate a BI extract.
        
        Args:
            extract_id: ID of registered extract
            params: Optional parameters (date range, filters, etc.)
            
        Returns:
            Extract result with data and metadata
        """
        config = self._extract_configs.get(extract_id)
        if not config:
            raise ValueError(f"Unknown extract: {extract_id}")

        # Generate data based on query type
        data = self._query_data(config["query_type"], params or {})
        
        # Format output
        if config["output_format"] == "json":
            output = data
        elif config["output_format"] == "csv":
            output = self._to_csv(data)
        else:
            output = data

        # Update last run
        config["last_run"] = datetime.utcnow()

        return {
            "extract_id": extract_id,
            "name": config["name"],
            "generated_at": datetime.utcnow().isoformat(),
            "record_count": len(data) if isinstance(data, list) else 1,
            "format": config["output_format"],
            "data": output
        }

    def _query_data(self, query_type: str, params: Dict) -> List[Dict]:
        """Query data for extract (would use DB in production)."""
        # Mock data for demo
        if query_type == "schedule":
            return [
                {"period": "2026-01-06 Day", "planned_tonnes": 45000, "resource_count": 12},
                {"period": "2026-01-06 Night", "planned_tonnes": 42000, "resource_count": 10}
            ]
        elif query_type == "quality":
            return [
                {"product": "Coal", "cv_avg": 25.3, "ash_avg": 14.2, "compliance": 0.95}
            ]
        return []

    def _to_csv(self, data: List[Dict]) -> str:
        """Convert data to CSV format."""
        if not data:
            return ""
        headers = list(data[0].keys())
        lines = [",".join(headers)]
        for row in data:
            lines.append(",".join(str(row.get(h, "")) for h in headers))
        return "\n".join(lines)

    def list_extracts(self) -> List[Dict]:
        """List all registered extracts."""
        return [
            {
                "extract_id": eid,
                "name": config["name"],
                "query_type": config["query_type"],
                "format": config["output_format"],
                "last_run": config["last_run"].isoformat() if config["last_run"] else None
            }
            for eid, config in self._extract_configs.items()
        ]
