"""Tests for the 1080 data processor."""

import pytest
from datetime import date
from decimal import Decimal

from processor_1080.models import (
    Record1080,
    RecordStatus,
    RecordType,
    ProcessingConfig,
    ProcessingResult,
)
from processor_1080.processor import Processor1080


class TestRecord1080:
    """Tests for the Record1080 model."""

    def test_create_record(self):
        """Test creating a basic record."""
        record = Record1080(
            record_id="TEST-001",
            entity_name="Test Company",
            entity_id="12-3456789",
            amount=Decimal("1000.00"),
            transaction_date=date(2024, 1, 15),
            reporting_period="2024-Q1",
        )

        assert record.record_id == "TEST-001"
        assert record.entity_name == "Test Company"
        assert record.amount == Decimal("1000.00")
        assert record.status == RecordStatus.PENDING

    def test_parse_amount_from_string(self):
        """Test parsing amounts from string formats."""
        record = Record1080(
            record_id="TEST-001",
            entity_name="Test Company",
            entity_id="12-3456789",
            amount="$1,234.56",
            transaction_date=date(2024, 1, 15),
            reporting_period="2024-Q1",
        )

        assert record.amount == Decimal("1234.56")

    def test_calculate_net_amount(self):
        """Test net amount calculation."""
        record = Record1080(
            record_id="TEST-001",
            entity_name="Test Company",
            entity_id="12-3456789",
            amount=Decimal("1000.00"),
            secondary_amount=Decimal("200.00"),
            adjustment_amount=Decimal("-50.00"),
            transaction_date=date(2024, 1, 15),
            reporting_period="2024-Q1",
        )

        assert record.calculate_net_amount() == Decimal("1150.00")

    def test_state_normalization(self):
        """Test state code normalization to uppercase."""
        record = Record1080(
            record_id="TEST-001",
            entity_name="Test Company",
            entity_id="12-3456789",
            entity_state="ny",
            amount=Decimal("1000.00"),
            transaction_date=date(2024, 1, 15),
            reporting_period="2024-Q1",
        )

        assert record.entity_state == "NY"


class TestProcessor1080:
    """Tests for the Processor1080 class."""

    def test_validate_valid_record(self):
        """Test validation of a valid record."""
        processor = Processor1080()
        record = Record1080(
            record_id="TEST-001",
            entity_name="Test Company",
            entity_id="12-3456789",
            entity_state="NY",
            entity_zip="10001",
            amount=Decimal("1000.00"),
            transaction_date=date(2024, 1, 15),
            reporting_period="2024-Q1",
        )

        errors = processor.validate_record(record)
        critical_errors = [e for e in errors if e.severity == "error"]

        assert len(critical_errors) == 0

    def test_validate_missing_entity_name(self):
        """Test validation fails for missing entity name."""
        processor = Processor1080()
        record = Record1080(
            record_id="TEST-001",
            entity_name="",
            entity_id="12-3456789",
            amount=Decimal("1000.00"),
            transaction_date=date(2024, 1, 15),
            reporting_period="2024-Q1",
        )

        errors = processor.validate_record(record)

        assert any(e.field == "entity_name" for e in errors)

    def test_validate_invalid_state_code(self):
        """Test validation warns for invalid state code."""
        processor = Processor1080()
        record = Record1080(
            record_id="TEST-001",
            entity_name="Test Company",
            entity_id="12-3456789",
            entity_state="XX",
            amount=Decimal("1000.00"),
            transaction_date=date(2024, 1, 15),
            reporting_period="2024-Q1",
        )

        errors = processor.validate_record(record)

        state_errors = [e for e in errors if e.field == "entity_state"]
        assert len(state_errors) == 1
        assert state_errors[0].severity == "warning"

    def test_validate_negative_amount_not_allowed(self):
        """Test validation fails for negative amounts when not allowed."""
        config = ProcessingConfig(allow_negative_amounts=False)
        processor = Processor1080(config)
        record = Record1080(
            record_id="TEST-001",
            entity_name="Test Company",
            entity_id="12-3456789",
            amount=Decimal("-100.00"),
            transaction_date=date(2024, 1, 15),
            reporting_period="2024-Q1",
        )

        errors = processor.validate_record(record)

        assert any(e.field == "amount" for e in errors)

    def test_validate_negative_amount_allowed(self):
        """Test validation passes for negative amounts when allowed."""
        config = ProcessingConfig(allow_negative_amounts=True)
        processor = Processor1080(config)
        record = Record1080(
            record_id="TEST-001",
            entity_name="Test Company",
            entity_id="12-3456789",
            amount=Decimal("-100.00"),
            transaction_date=date(2024, 1, 15),
            reporting_period="2024-Q1",
        )

        errors = processor.validate_record(record)

        assert not any(e.field == "amount" and e.severity == "error" for e in errors)

    def test_process_record(self):
        """Test processing a single record."""
        processor = Processor1080()
        record = Record1080(
            record_id="TEST-001",
            entity_name="Test Company",
            entity_id="12-3456789",
            amount=Decimal("1000.00"),
            transaction_date=date(2024, 1, 15),
            reporting_period="2024-Q1",
        )

        processed, errors = processor.process_record(record)

        assert processed.status == RecordStatus.PROCESSED
        assert processed.processed_at is not None

    def test_process_batch(self):
        """Test batch processing of records."""
        processor = Processor1080()
        records = [
            Record1080(
                record_id=f"TEST-{i:03d}",
                entity_name=f"Company {i}",
                entity_id=f"12-345678{i}",
                amount=Decimal(str(1000 * i)),
                transaction_date=date(2024, 1, 15),
                reporting_period="2024-Q1",
            )
            for i in range(1, 6)
        ]

        result = processor.process_batch(records)

        assert result.total_records == 5
        assert result.successful == 5
        assert result.failed == 0

    def test_aggregate_by_entity(self):
        """Test aggregation by entity."""
        processor = Processor1080()
        records = [
            Record1080(
                record_id="TEST-001",
                entity_name="Company A",
                entity_id="12-3456789",
                amount=Decimal("1000.00"),
                transaction_date=date(2024, 1, 15),
                reporting_period="2024-Q1",
            ),
            Record1080(
                record_id="TEST-002",
                entity_name="Company A",
                entity_id="12-3456789",
                amount=Decimal("2000.00"),
                transaction_date=date(2024, 2, 15),
                reporting_period="2024-Q1",
            ),
            Record1080(
                record_id="TEST-003",
                entity_name="Company B",
                entity_id="98-7654321",
                amount=Decimal("500.00"),
                transaction_date=date(2024, 1, 20),
                reporting_period="2024-Q1",
            ),
        ]

        aggregated = processor.aggregate_by_entity(records)

        assert len(aggregated) == 2
        assert aggregated["12-3456789"]["total_amount"] == Decimal("3000.00")
        assert aggregated["12-3456789"]["record_count"] == 2
        assert aggregated["98-7654321"]["total_amount"] == Decimal("500.00")


class TestProcessingConfig:
    """Tests for ProcessingConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ProcessingConfig()

        assert config.validate_entities is True
        assert config.validate_amounts is True
        assert config.allow_negative_amounts is False
        assert config.skip_invalid is False
        assert config.output_format == "csv"

    def test_custom_config(self):
        """Test custom configuration."""
        config = ProcessingConfig(
            allow_negative_amounts=True,
            skip_invalid=True,
            output_format="json",
        )

        assert config.allow_negative_amounts is True
        assert config.skip_invalid is True
        assert config.output_format == "json"
