"""
File handling for 1080 data processing.

This module provides functionality for reading and writing
1080 data in various file formats (CSV, Excel, JSON).
"""

import csv
import json
import logging
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

import pandas as pd

from .models import Record1080, ProcessingResult, ProcessingConfig

logger = logging.getLogger(__name__)


class FileHandler:
    """
    Handles file I/O operations for 1080 data.

    Supports reading from and writing to CSV, Excel, and JSON formats.
    """

    # Column mappings for common variations
    COLUMN_MAPPINGS = {
        # Entity fields
        "entity_name": ["entity_name", "name", "company_name", "organization", "entity"],
        "entity_id": ["entity_id", "ein", "tax_id", "id", "tin"],
        "entity_address": ["entity_address", "address", "street_address", "address_line_1"],
        "entity_city": ["entity_city", "city"],
        "entity_state": ["entity_state", "state", "state_code"],
        "entity_zip": ["entity_zip", "zip", "zip_code", "postal_code"],
        # Financial fields
        "amount": ["amount", "total_amount", "gross_amount", "payment_amount"],
        "secondary_amount": ["secondary_amount", "additional_amount", "other_amount"],
        "adjustment_amount": ["adjustment_amount", "adjustment", "withholding"],
        # Date fields
        "transaction_date": ["transaction_date", "date", "payment_date", "tx_date"],
        "reporting_period": ["reporting_period", "period", "quarter", "tax_period"],
        # Other fields
        "record_id": ["record_id", "id", "record_number", "ref_id"],
        "record_type": ["record_type", "type"],
        "notes": ["notes", "comments", "remarks"],
    }

    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        Initialize the file handler.

        Args:
            config: Optional processing configuration.
        """
        self.config = config or ProcessingConfig()

    def read_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Read data from a file.

        Args:
            file_path: Path to the input file.

        Returns:
            List of dictionaries representing records.

        Raises:
            ValueError: If file format is not supported.
            FileNotFoundError: If file does not exist.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = path.suffix.lower()

        if extension == ".csv":
            return self._read_csv(path)
        elif extension in [".xlsx", ".xls"]:
            return self._read_excel(path)
        elif extension == ".json":
            return self._read_json(path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def _read_csv(self, path: Path) -> List[Dict[str, Any]]:
        """Read data from a CSV file."""
        logger.info(f"Reading CSV file: {path}")

        df = pd.read_csv(path, dtype=str)
        df = self._normalize_columns(df)

        records = df.to_dict("records")
        logger.info(f"Read {len(records)} records from CSV")

        return records

    def _read_excel(self, path: Path) -> List[Dict[str, Any]]:
        """Read data from an Excel file."""
        logger.info(f"Reading Excel file: {path}")

        df = pd.read_excel(path, dtype=str)
        df = self._normalize_columns(df)

        records = df.to_dict("records")
        logger.info(f"Read {len(records)} records from Excel")

        return records

    def _read_json(self, path: Path) -> List[Dict[str, Any]]:
        """Read data from a JSON file."""
        logger.info(f"Reading JSON file: {path}")

        with open(path, "r") as f:
            data = json.load(f)

        # Handle both list and single object
        if isinstance(data, dict):
            if "records" in data:
                records = data["records"]
            else:
                records = [data]
        else:
            records = data

        logger.info(f"Read {len(records)} records from JSON")

        return records

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to match expected fields."""
        # Convert column names to lowercase and strip whitespace
        df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")

        # Map columns to standard names
        rename_map = {}
        for standard_name, variations in self.COLUMN_MAPPINGS.items():
            for variation in variations:
                if variation in df.columns and standard_name not in df.columns:
                    rename_map[variation] = standard_name
                    break

        if rename_map:
            df = df.rename(columns=rename_map)
            logger.debug(f"Renamed columns: {rename_map}")

        return df

    def write_file(
        self,
        records: List[Record1080],
        file_path: Union[str, Path],
        format: Optional[str] = None,
    ) -> Path:
        """
        Write records to a file.

        Args:
            records: List of records to write.
            file_path: Output file path.
            format: Output format (csv, xlsx, json). Auto-detected from extension if not provided.

        Returns:
            Path to the written file.
        """
        path = Path(file_path)

        # Determine format
        if format is None:
            format = path.suffix.lower().lstrip(".")

        # Convert records to dictionaries
        data = [self._record_to_dict(r) for r in records]

        if format == "csv":
            return self._write_csv(data, path)
        elif format in ["xlsx", "xls", "excel"]:
            return self._write_excel(data, path)
        elif format == "json":
            return self._write_json(data, path)
        else:
            raise ValueError(f"Unsupported output format: {format}")

    def _record_to_dict(self, record: Record1080) -> Dict[str, Any]:
        """Convert a record to a dictionary for export."""
        data = record.to_dict()

        # Remove metadata if not configured to include
        if not self.config.include_metadata:
            data.pop("metadata", None)
            data.pop("created_at", None)
            data.pop("processed_at", None)
            data.pop("source_file", None)

        return data

    def _write_csv(self, data: List[Dict[str, Any]], path: Path) -> Path:
        """Write data to a CSV file."""
        logger.info(f"Writing {len(data)} records to CSV: {path}")

        if not data:
            logger.warning("No data to write")
            return path

        df = pd.DataFrame(data)
        df.to_csv(path, index=False)

        logger.info(f"Successfully wrote CSV file: {path}")
        return path

    def _write_excel(self, data: List[Dict[str, Any]], path: Path) -> Path:
        """Write data to an Excel file."""
        logger.info(f"Writing {len(data)} records to Excel: {path}")

        if not data:
            logger.warning("No data to write")
            return path

        # Ensure .xlsx extension
        if path.suffix.lower() != ".xlsx":
            path = path.with_suffix(".xlsx")

        df = pd.DataFrame(data)
        df.to_excel(path, index=False, engine="openpyxl")

        logger.info(f"Successfully wrote Excel file: {path}")
        return path

    def _write_json(self, data: List[Dict[str, Any]], path: Path) -> Path:
        """Write data to a JSON file."""
        logger.info(f"Writing {len(data)} records to JSON: {path}")

        output = {
            "generated_at": datetime.now().isoformat(),
            "record_count": len(data),
            "records": data,
        }

        with open(path, "w") as f:
            json.dump(output, f, indent=2, default=str)

        logger.info(f"Successfully wrote JSON file: {path}")
        return path

    def write_result(
        self,
        result: ProcessingResult,
        output_dir: Union[str, Path],
        base_name: str = "processed_1080",
    ) -> Dict[str, Path]:
        """
        Write processing result to multiple files.

        Args:
            result: The processing result to write.
            output_dir: Directory for output files.
            base_name: Base name for output files.

        Returns:
            Dictionary mapping file types to their paths.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Write processed records
        records_path = output_dir / f"{base_name}_{timestamp}.{self.config.output_format}"
        self.write_file(result.processed_records, records_path)
        output_files["records"] = records_path

        # Write summary
        summary_path = output_dir / f"{base_name}_{timestamp}_summary.json"
        self._write_summary(result, summary_path)
        output_files["summary"] = summary_path

        # Write errors if any
        if result.errors:
            errors_path = output_dir / f"{base_name}_{timestamp}_errors.csv"
            self._write_errors(result.errors, errors_path)
            output_files["errors"] = errors_path

        return output_files

    def _write_summary(self, result: ProcessingResult, path: Path) -> None:
        """Write processing summary to JSON."""
        from .processor import Processor1080

        processor = Processor1080(self.config)
        summary = processor.generate_summary(result)

        with open(path, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Wrote summary to: {path}")

    def _write_errors(self, errors: List[Any], path: Path) -> None:
        """Write errors to CSV."""
        error_data = [
            {
                "record_id": e.record_id,
                "field": e.field,
                "message": e.message,
                "severity": e.severity,
            }
            for e in errors
        ]

        df = pd.DataFrame(error_data)
        df.to_csv(path, index=False)

        logger.info(f"Wrote errors to: {path}")


def load_from_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Convenience function to load data from a file.

    Args:
        file_path: Path to the input file.

    Returns:
        List of dictionaries representing records.
    """
    handler = FileHandler()
    return handler.read_file(file_path)


def save_to_file(
    records: List[Record1080],
    file_path: Union[str, Path],
    format: Optional[str] = None,
) -> Path:
    """
    Convenience function to save records to a file.

    Args:
        records: List of records to save.
        file_path: Output file path.
        format: Optional output format.

    Returns:
        Path to the written file.
    """
    handler = FileHandler()
    return handler.write_file(records, file_path, format)
