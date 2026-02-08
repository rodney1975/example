import os
import pytest

from src.data.models import SprintRecord
from src.data.parser import parse_csv, parse_directory


class TestParseCsv:
    def test_parse_csv_returns_records(self, sample_csv_path):
        records = parse_csv(sample_csv_path)
        assert isinstance(records, list), "parse_csv should return a list"
        assert len(records) > 0, "parse_csv should return a non-empty list"
        assert all(
            isinstance(r, SprintRecord) for r in records
        ), "all items should be SprintRecord instances"

    def test_parse_csv_record_count(self, sample_csv_path):
        records = parse_csv(sample_csv_path)
        assert len(records) == 38, (
            f"sprint_session_001.csv should have 38 records, got {len(records)}"
        )

    def test_parse_csv_first_record_values(self, sample_csv_path):
        records = parse_csv(sample_csv_path)
        first = records[0]
        assert first.rep == 1, f"first record rep should be 1, got {first.rep}"
        assert first.timestamp == 0.0, (
            f"first record timestamp should be 0.0, got {first.timestamp}"
        )
        assert first.velocity == 0.0, (
            f"first record velocity should be 0.0, got {first.velocity}"
        )
        assert first.stroke_phase == "Glide", (
            f"first record stroke_phase should be 'Glide', got '{first.stroke_phase}'"
        )

    def test_parse_csv_handles_unicode_minus(self, sample_csv_path):
        records = parse_csv(sample_csv_path)
        negative_accel_records = [r for r in records if r.acceleration < 0]
        assert len(negative_accel_records) > 0, (
            "should have records with negative acceleration values "
            "(parsed from Unicode minus signs)"
        )
        rec_with_neg = next(
            r for r in records
            if r.rep == 1 and r.timestamp == pytest.approx(0.4, abs=0.001)
        )
        assert rec_with_neg.acceleration == pytest.approx(-1.60, abs=0.01), (
            f"acceleration should be -1.60, got {rec_with_neg.acceleration}"
        )

    def test_parse_csv_column_types(self, sample_csv_path):
        records = parse_csv(sample_csv_path)
        for rec in records:
            assert isinstance(rec.rep, int), (
                f"rep should be int, got {type(rec.rep).__name__}"
            )
            assert isinstance(rec.timestamp, float), (
                f"timestamp should be float, got {type(rec.timestamp).__name__}"
            )
            assert isinstance(rec.position, float), (
                f"position should be float, got {type(rec.position).__name__}"
            )
            assert isinstance(rec.velocity, float), (
                f"velocity should be float, got {type(rec.velocity).__name__}"
            )
            assert isinstance(rec.acceleration, float), (
                f"acceleration should be float, got {type(rec.acceleration).__name__}"
            )
            assert isinstance(rec.force, float), (
                f"force should be float, got {type(rec.force).__name__}"
            )
            assert isinstance(rec.power, float), (
                f"power should be float, got {type(rec.power).__name__}"
            )

    def test_parse_csv_invalid_file(self):
        with pytest.raises(FileNotFoundError):
            parse_csv("/nonexistent/path/fake_file.csv")


class TestParseDirectory:
    def test_parse_directory(self, sample_data_dir):
        result = parse_directory(sample_data_dir)
        assert isinstance(result, dict), "parse_directory should return a dict"
        assert "sprint_session_001.csv" in result, (
            "result should contain sprint_session_001.csv"
        )
        assert "sprint_session_002.csv" in result, (
            "result should contain sprint_session_002.csv"
        )
        for filename, records in result.items():
            assert isinstance(records, list), (
                f"records for {filename} should be a list"
            )
            assert all(
                isinstance(r, SprintRecord) for r in records
            ), f"all records for {filename} should be SprintRecord instances"

    def test_parse_directory_record_counts(self, sample_data_dir):
        result = parse_directory(sample_data_dir)
        expected_counts = {
            "sprint_session_001.csv": 38,
            "sprint_session_002.csv": 26,
        }
        for filename, expected_count in expected_counts.items():
            assert filename in result, f"{filename} should be in results"
            actual_count = len(result[filename])
            assert actual_count == expected_count, (
                f"{filename} should have {expected_count} records, got {actual_count}"
            )
