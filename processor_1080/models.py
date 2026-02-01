"""
Data models for 1080 data processing.

This module defines the core data structures used throughout
the 1080 data processing application.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class RecordStatus(str, Enum):
    """Status of a 1080 record."""
    PENDING = "pending"
    VALIDATED = "validated"
    PROCESSED = "processed"
    ERROR = "error"
    EXPORTED = "exported"


class RecordType(str, Enum):
    """Type of 1080 record."""
    STANDARD = "standard"
    AMENDED = "amended"
    CORRECTED = "corrected"
    VOID = "void"


class Record1080(BaseModel):
    """
    Represents a single 1080 data record.

    This model captures all the essential fields for a 1080 record
    including identification, financial data, and metadata.
    """

    record_id: str = Field(..., description="Unique identifier for the record")
    record_type: RecordType = Field(default=RecordType.STANDARD, description="Type of record")

    # Entity information
    entity_name: str = Field(..., min_length=1, description="Name of the entity")
    entity_id: str = Field(..., description="Entity identification number")
    entity_address: Optional[str] = Field(default=None, description="Entity address")
    entity_city: Optional[str] = Field(default=None, description="Entity city")
    entity_state: Optional[str] = Field(default=None, max_length=2, description="Entity state code")
    entity_zip: Optional[str] = Field(default=None, description="Entity ZIP code")

    # Financial data
    amount: Decimal = Field(..., description="Primary amount")
    secondary_amount: Optional[Decimal] = Field(default=None, description="Secondary amount")
    adjustment_amount: Optional[Decimal] = Field(default=Decimal("0"), description="Adjustment amount")

    # Dates
    transaction_date: date = Field(..., description="Date of transaction")
    reporting_period: str = Field(..., description="Reporting period (e.g., '2024-Q1')")

    # Processing metadata
    status: RecordStatus = Field(default=RecordStatus.PENDING, description="Processing status")
    source_file: Optional[str] = Field(default=None, description="Source file name")
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation timestamp")
    processed_at: Optional[datetime] = Field(default=None, description="Processing timestamp")

    # Additional data
    notes: Optional[str] = Field(default=None, description="Additional notes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("entity_state")
    @classmethod
    def validate_state_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize state code to uppercase."""
        if v is not None:
            return v.upper()
        return v

    @field_validator("amount", "secondary_amount", "adjustment_amount", mode="before")
    @classmethod
    def parse_decimal(cls, v: Any) -> Optional[Decimal]:
        """Parse decimal values from various formats."""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            # Remove currency symbols and commas
            cleaned = v.replace("$", "").replace(",", "").strip()
            if cleaned == "" or cleaned == "-":
                return Decimal("0")
            return Decimal(cleaned)
        return v

    def calculate_net_amount(self) -> Decimal:
        """Calculate net amount after adjustments."""
        base = self.amount
        if self.secondary_amount:
            base += self.secondary_amount
        if self.adjustment_amount:
            base += self.adjustment_amount
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for export."""
        data = self.model_dump()
        # Convert Decimal to float for JSON serialization
        for key in ["amount", "secondary_amount", "adjustment_amount"]:
            if data[key] is not None:
                data[key] = float(data[key])
        # Convert dates to ISO format
        if data["transaction_date"]:
            data["transaction_date"] = data["transaction_date"].isoformat()
        if data["created_at"]:
            data["created_at"] = data["created_at"].isoformat()
        if data["processed_at"]:
            data["processed_at"] = data["processed_at"].isoformat()
        return data


class ValidationError(BaseModel):
    """Represents a validation error for a record."""

    record_id: str = Field(..., description="ID of the record with error")
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    severity: str = Field(default="error", description="Error severity (error, warning)")


class ProcessingResult(BaseModel):
    """
    Result of processing a batch of 1080 records.

    Contains statistics and details about the processing operation.
    """

    total_records: int = Field(default=0, description="Total records processed")
    successful: int = Field(default=0, description="Successfully processed records")
    failed: int = Field(default=0, description="Failed records")
    warnings: int = Field(default=0, description="Records with warnings")

    processed_records: List[Record1080] = Field(default_factory=list, description="Processed records")
    errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")

    processing_time_seconds: float = Field(default=0.0, description="Processing time in seconds")
    started_at: Optional[datetime] = Field(default=None, description="Processing start time")
    completed_at: Optional[datetime] = Field(default=None, description="Processing completion time")

    def add_record(self, record: Record1080) -> None:
        """Add a successfully processed record."""
        self.processed_records.append(record)
        self.successful += 1
        self.total_records += 1

    def add_error(self, error: ValidationError) -> None:
        """Add a validation error."""
        self.errors.append(error)
        if error.severity == "error":
            self.failed += 1
        else:
            self.warnings += 1
        self.total_records += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the processing result."""
        return {
            "total_records": self.total_records,
            "successful": self.successful,
            "failed": self.failed,
            "warnings": self.warnings,
            "success_rate": f"{(self.successful / self.total_records * 100):.1f}%" if self.total_records > 0 else "N/A",
            "processing_time": f"{self.processing_time_seconds:.2f}s",
        }


class ProcessingConfig(BaseModel):
    """Configuration for 1080 data processing."""

    validate_entities: bool = Field(default=True, description="Validate entity information")
    validate_amounts: bool = Field(default=True, description="Validate financial amounts")
    allow_negative_amounts: bool = Field(default=False, description="Allow negative amounts")
    require_address: bool = Field(default=False, description="Require complete address")
    date_format: str = Field(default="%Y-%m-%d", description="Expected date format")
    decimal_places: int = Field(default=2, description="Decimal places for amounts")
    skip_invalid: bool = Field(default=False, description="Skip invalid records instead of failing")

    # Output settings
    output_format: str = Field(default="csv", description="Output format (csv, xlsx, json)")
    include_metadata: bool = Field(default=True, description="Include metadata in output")
