"""
Core processor for 1080 data.

This module contains the main processing logic for validating,
transforming, and processing 1080 records.
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional, Callable
import logging

from .models import (
    Record1080,
    RecordStatus,
    RecordType,
    ProcessingResult,
    ProcessingConfig,
    ValidationError,
)

logger = logging.getLogger(__name__)


class Processor1080:
    """
    Main processor for 1080 data records.

    Handles validation, transformation, and processing of 1080 data
    according to specified configuration rules.
    """

    # Valid US state codes
    VALID_STATES = {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        "DC", "PR", "VI", "GU", "AS", "MP",
    }

    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        Initialize the processor with optional configuration.

        Args:
            config: Processing configuration. Uses defaults if not provided.
        """
        self.config = config or ProcessingConfig()
        self._custom_validators: List[Callable[[Record1080], Optional[ValidationError]]] = []

    def add_validator(self, validator: Callable[[Record1080], Optional[ValidationError]]) -> None:
        """
        Add a custom validation function.

        Args:
            validator: Function that takes a Record1080 and returns
                      a ValidationError if validation fails, None otherwise.
        """
        self._custom_validators.append(validator)

    def validate_record(self, record: Record1080) -> List[ValidationError]:
        """
        Validate a single 1080 record.

        Args:
            record: The record to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        # Validate entity information
        if self.config.validate_entities:
            entity_errors = self._validate_entity(record)
            errors.extend(entity_errors)

        # Validate amounts
        if self.config.validate_amounts:
            amount_errors = self._validate_amounts(record)
            errors.extend(amount_errors)

        # Validate address if required
        if self.config.require_address:
            address_errors = self._validate_address(record)
            errors.extend(address_errors)

        # Run custom validators
        for validator in self._custom_validators:
            error = validator(record)
            if error:
                errors.append(error)

        return errors

    def _validate_entity(self, record: Record1080) -> List[ValidationError]:
        """Validate entity information."""
        errors = []

        # Validate entity ID format (basic check)
        if not record.entity_id or len(record.entity_id) < 2:
            errors.append(ValidationError(
                record_id=record.record_id,
                field="entity_id",
                message="Entity ID is required and must be at least 2 characters",
            ))

        # Validate entity name
        if not record.entity_name or record.entity_name.strip() == "":
            errors.append(ValidationError(
                record_id=record.record_id,
                field="entity_name",
                message="Entity name is required",
            ))

        # Validate state code if provided
        if record.entity_state and record.entity_state.upper() not in self.VALID_STATES:
            errors.append(ValidationError(
                record_id=record.record_id,
                field="entity_state",
                message=f"Invalid state code: {record.entity_state}",
                severity="warning",
            ))

        # Validate ZIP code format if provided
        if record.entity_zip:
            zip_pattern = r"^\d{5}(-\d{4})?$"
            if not re.match(zip_pattern, record.entity_zip):
                errors.append(ValidationError(
                    record_id=record.record_id,
                    field="entity_zip",
                    message=f"Invalid ZIP code format: {record.entity_zip}",
                    severity="warning",
                ))

        return errors

    def _validate_amounts(self, record: Record1080) -> List[ValidationError]:
        """Validate financial amounts."""
        errors = []

        # Check for negative amounts
        if not self.config.allow_negative_amounts:
            if record.amount < 0:
                errors.append(ValidationError(
                    record_id=record.record_id,
                    field="amount",
                    message="Negative amounts are not allowed",
                ))
            if record.secondary_amount and record.secondary_amount < 0:
                errors.append(ValidationError(
                    record_id=record.record_id,
                    field="secondary_amount",
                    message="Negative secondary amounts are not allowed",
                ))

        # Validate decimal places
        decimal_places = self.config.decimal_places
        if record.amount is not None:
            _, _, exponent = record.amount.as_tuple()
            if isinstance(exponent, int) and abs(exponent) > decimal_places:
                errors.append(ValidationError(
                    record_id=record.record_id,
                    field="amount",
                    message=f"Amount has more than {decimal_places} decimal places",
                    severity="warning",
                ))

        return errors

    def _validate_address(self, record: Record1080) -> List[ValidationError]:
        """Validate address completeness."""
        errors = []
        missing_fields = []

        if not record.entity_address:
            missing_fields.append("address")
        if not record.entity_city:
            missing_fields.append("city")
        if not record.entity_state:
            missing_fields.append("state")
        if not record.entity_zip:
            missing_fields.append("zip")

        if missing_fields:
            errors.append(ValidationError(
                record_id=record.record_id,
                field="address",
                message=f"Missing address fields: {', '.join(missing_fields)}",
            ))

        return errors

    def process_record(self, record: Record1080) -> tuple[Record1080, List[ValidationError]]:
        """
        Process a single record.

        Args:
            record: The record to process.

        Returns:
            Tuple of (processed record, list of errors).
        """
        errors = self.validate_record(record)

        # Determine if we should continue processing
        has_critical_errors = any(e.severity == "error" for e in errors)

        if has_critical_errors and not self.config.skip_invalid:
            record.status = RecordStatus.ERROR
            return record, errors

        # Apply transformations
        record = self._transform_record(record)

        # Mark as processed
        record.status = RecordStatus.PROCESSED if not has_critical_errors else RecordStatus.ERROR
        record.processed_at = datetime.now()

        return record, errors

    def _transform_record(self, record: Record1080) -> Record1080:
        """Apply transformations to a record."""
        # Round amounts to configured decimal places
        if record.amount is not None:
            record.amount = round(record.amount, self.config.decimal_places)
        if record.secondary_amount is not None:
            record.secondary_amount = round(record.secondary_amount, self.config.decimal_places)
        if record.adjustment_amount is not None:
            record.adjustment_amount = round(record.adjustment_amount, self.config.decimal_places)

        # Normalize entity name (title case)
        if record.entity_name:
            record.entity_name = record.entity_name.strip()

        # Normalize state code
        if record.entity_state:
            record.entity_state = record.entity_state.upper()

        return record

    def process_batch(self, records: List[Record1080]) -> ProcessingResult:
        """
        Process a batch of records.

        Args:
            records: List of records to process.

        Returns:
            ProcessingResult with statistics and processed records.
        """
        result = ProcessingResult()
        result.started_at = datetime.now()

        for record in records:
            processed_record, errors = self.process_record(record)

            if processed_record.status == RecordStatus.ERROR:
                for error in errors:
                    result.add_error(error)
            else:
                result.add_record(processed_record)
                # Add warnings
                for error in errors:
                    if error.severity == "warning":
                        result.errors.append(error)
                        result.warnings += 1

        result.completed_at = datetime.now()
        result.processing_time_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()

        logger.info(
            f"Processed {result.total_records} records: "
            f"{result.successful} successful, {result.failed} failed, "
            f"{result.warnings} warnings"
        )

        return result

    def process_raw_data(self, data: List[Dict[str, Any]]) -> ProcessingResult:
        """
        Process raw dictionary data.

        Args:
            data: List of dictionaries representing records.

        Returns:
            ProcessingResult with statistics and processed records.
        """
        records = []
        parse_errors = []

        for idx, row in enumerate(data):
            try:
                record = self._parse_raw_record(row, idx)
                records.append(record)
            except Exception as e:
                parse_errors.append(ValidationError(
                    record_id=row.get("record_id", f"row_{idx}"),
                    field="parsing",
                    message=str(e),
                ))

        result = self.process_batch(records)

        # Add parsing errors
        for error in parse_errors:
            result.add_error(error)

        return result

    def _parse_raw_record(self, data: Dict[str, Any], index: int) -> Record1080:
        """Parse a raw dictionary into a Record1080."""
        # Generate record ID if not present
        if "record_id" not in data:
            data["record_id"] = f"REC-{index:06d}"

        # Parse transaction date
        if "transaction_date" in data:
            date_val = data["transaction_date"]
            if isinstance(date_val, str):
                from dateutil import parser as date_parser
                data["transaction_date"] = date_parser.parse(date_val).date()

        # Set default reporting period if not present
        if "reporting_period" not in data:
            if "transaction_date" in data:
                tx_date = data["transaction_date"]
                quarter = (tx_date.month - 1) // 3 + 1
                data["reporting_period"] = f"{tx_date.year}-Q{quarter}"
            else:
                data["reporting_period"] = datetime.now().strftime("%Y-Q1")

        return Record1080(**data)

    def aggregate_by_entity(self, records: List[Record1080]) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate records by entity.

        Args:
            records: List of processed records.

        Returns:
            Dictionary with entity_id as key and aggregated data as value.
        """
        aggregated = {}

        for record in records:
            entity_id = record.entity_id

            if entity_id not in aggregated:
                aggregated[entity_id] = {
                    "entity_id": entity_id,
                    "entity_name": record.entity_name,
                    "total_amount": Decimal("0"),
                    "total_secondary_amount": Decimal("0"),
                    "total_adjustment": Decimal("0"),
                    "record_count": 0,
                    "records": [],
                }

            agg = aggregated[entity_id]
            agg["total_amount"] += record.amount or Decimal("0")
            agg["total_secondary_amount"] += record.secondary_amount or Decimal("0")
            agg["total_adjustment"] += record.adjustment_amount or Decimal("0")
            agg["record_count"] += 1
            agg["records"].append(record.record_id)

        return aggregated

    def generate_summary(self, result: ProcessingResult) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of processing results.

        Args:
            result: The processing result to summarize.

        Returns:
            Dictionary containing summary statistics.
        """
        total_amount = sum(
            r.amount for r in result.processed_records if r.amount
        )
        total_secondary = sum(
            r.secondary_amount for r in result.processed_records
            if r.secondary_amount
        )

        # Group by reporting period
        by_period = {}
        for record in result.processed_records:
            period = record.reporting_period
            if period not in by_period:
                by_period[period] = {"count": 0, "amount": Decimal("0")}
            by_period[period]["count"] += 1
            by_period[period]["amount"] += record.amount or Decimal("0")

        # Group by record type
        by_type = {}
        for record in result.processed_records:
            rec_type = record.record_type.value
            if rec_type not in by_type:
                by_type[rec_type] = 0
            by_type[rec_type] += 1

        return {
            "processing_summary": result.get_summary(),
            "financial_totals": {
                "total_amount": float(total_amount),
                "total_secondary_amount": float(total_secondary),
                "net_total": float(total_amount + total_secondary),
            },
            "by_reporting_period": {
                k: {"count": v["count"], "amount": float(v["amount"])}
                for k, v in by_period.items()
            },
            "by_record_type": by_type,
            "error_summary": {
                "total_errors": len(result.errors),
                "by_field": self._group_errors_by_field(result.errors),
            },
        }

    def _group_errors_by_field(self, errors: List[ValidationError]) -> Dict[str, int]:
        """Group errors by field name."""
        by_field = {}
        for error in errors:
            if error.field not in by_field:
                by_field[error.field] = 0
            by_field[error.field] += 1
        return by_field
