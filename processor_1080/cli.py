"""
Command-line interface for 1080 data processor.

This module provides the CLI for processing 1080 data files.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from tabulate import tabulate

from .models import ProcessingConfig
from .processor import Processor1080
from .file_handler import FileHandler


def setup_logging(verbose: bool, quiet: bool) -> None:
    """Configure logging based on verbosity settings."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.group()
@click.version_option(version="1.0.0", prog_name="processor-1080")
def main():
    """
    1080 Data Processor - Process and validate 1080 data files.

    This tool processes 1080 data from CSV, Excel, or JSON files,
    validates the records, and exports them in various formats.
    """
    pass


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path. If not specified, outputs to stdout.",
)
@click.option(
    "-f", "--format",
    type=click.Choice(["csv", "xlsx", "json"]),
    default="csv",
    help="Output format (default: csv).",
)
@click.option(
    "--validate-only",
    is_flag=True,
    help="Only validate, don't process.",
)
@click.option(
    "--skip-invalid",
    is_flag=True,
    help="Skip invalid records instead of failing.",
)
@click.option(
    "--allow-negative",
    is_flag=True,
    help="Allow negative amounts.",
)
@click.option(
    "--require-address",
    is_flag=True,
    help="Require complete address information.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Enable verbose output.",
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress non-error output.",
)
def process(
    input_file: str,
    output: Optional[str],
    format: str,
    validate_only: bool,
    skip_invalid: bool,
    allow_negative: bool,
    require_address: bool,
    verbose: bool,
    quiet: bool,
):
    """
    Process a 1080 data file.

    Reads the input file, validates and processes records,
    and outputs the results.

    INPUT_FILE: Path to the input file (CSV, Excel, or JSON).
    """
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)

    try:
        # Create configuration
        config = ProcessingConfig(
            skip_invalid=skip_invalid,
            allow_negative_amounts=allow_negative,
            require_address=require_address,
            output_format=format,
        )

        # Initialize components
        file_handler = FileHandler(config)
        processor = Processor1080(config)

        # Read input file
        if not quiet:
            click.echo(f"Reading input file: {input_file}")

        raw_data = file_handler.read_file(input_file)

        if not quiet:
            click.echo(f"Found {len(raw_data)} records")

        # Process data
        if validate_only:
            click.echo("Validation mode - checking records...")
            # Just validate without full processing
            from .models import Record1080
            errors = []
            for idx, row in enumerate(raw_data):
                try:
                    record = processor._parse_raw_record(row, idx)
                    record_errors = processor.validate_record(record)
                    errors.extend(record_errors)
                except Exception as e:
                    click.echo(f"Error parsing record {idx}: {e}", err=True)

            if errors:
                click.echo(f"\nFound {len(errors)} validation issues:")
                for error in errors[:20]:  # Show first 20
                    symbol = "!" if error.severity == "warning" else "X"
                    click.echo(f"  [{symbol}] {error.record_id}: {error.field} - {error.message}")
                if len(errors) > 20:
                    click.echo(f"  ... and {len(errors) - 20} more")
                sys.exit(1)
            else:
                click.echo("All records are valid!")
                sys.exit(0)

        # Full processing
        result = processor.process_raw_data(raw_data)

        # Output results
        if output:
            output_path = Path(output)
            file_handler.write_file(result.processed_records, output_path, format)
            if not quiet:
                click.echo(f"Wrote {result.successful} records to: {output_path}")
        else:
            # Output summary to stdout
            summary = result.get_summary()
            click.echo("\nProcessing Summary:")
            click.echo("-" * 40)
            for key, value in summary.items():
                click.echo(f"  {key}: {value}")

        # Show errors if any
        if result.errors and not quiet:
            click.echo(f"\nErrors ({len(result.errors)}):")
            for error in result.errors[:10]:
                symbol = "!" if error.severity == "warning" else "X"
                click.echo(f"  [{symbol}] {error.record_id}: {error.field} - {error.message}")
            if len(result.errors) > 10:
                click.echo(f"  ... and {len(result.errors) - 10} more")

        # Exit with error if there were failures
        if result.failed > 0 and not skip_invalid:
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during processing")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-o", "--output-dir",
    type=click.Path(),
    default="./output",
    help="Output directory for generated files.",
)
@click.option(
    "-f", "--format",
    type=click.Choice(["csv", "xlsx", "json"]),
    default="csv",
    help="Output format for processed records.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Enable verbose output.",
)
def batch(input_file: str, output_dir: str, format: str, verbose: bool):
    """
    Batch process a 1080 data file with full output.

    Generates processed records, summary, and error files.

    INPUT_FILE: Path to the input file (CSV, Excel, or JSON).
    """
    setup_logging(verbose, False)

    try:
        config = ProcessingConfig(
            skip_invalid=True,
            output_format=format,
        )

        file_handler = FileHandler(config)
        processor = Processor1080(config)

        click.echo(f"Reading: {input_file}")
        raw_data = file_handler.read_file(input_file)
        click.echo(f"Processing {len(raw_data)} records...")

        result = processor.process_raw_data(raw_data)

        # Write all output files
        output_files = file_handler.write_result(result, output_dir)

        click.echo("\nOutput files generated:")
        for file_type, path in output_files.items():
            click.echo(f"  {file_type}: {path}")

        # Show summary
        summary = result.get_summary()
        click.echo("\nProcessing Summary:")
        click.echo("-" * 40)
        for key, value in summary.items():
            click.echo(f"  {key}: {value}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-n", "--limit",
    type=int,
    default=10,
    help="Number of records to preview.",
)
def preview(input_file: str, limit: int):
    """
    Preview records from a 1080 data file.

    Shows a formatted table of records from the input file.

    INPUT_FILE: Path to the input file (CSV, Excel, or JSON).
    """
    try:
        file_handler = FileHandler()
        raw_data = file_handler.read_file(input_file)

        if not raw_data:
            click.echo("No records found in file.")
            return

        # Show limited records
        preview_data = raw_data[:limit]

        # Select key columns for display
        display_columns = [
            "record_id", "entity_name", "entity_id",
            "amount", "transaction_date", "reporting_period",
        ]

        # Filter to available columns
        available_cols = set(preview_data[0].keys())
        cols_to_show = [c for c in display_columns if c in available_cols]

        # Build table data
        table_data = []
        for row in preview_data:
            table_data.append([row.get(col, "") for col in cols_to_show])

        click.echo(f"\nPreview of {len(preview_data)} / {len(raw_data)} records:\n")
        click.echo(tabulate(table_data, headers=cols_to_show, tablefmt="grid"))

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file for the report (default: stdout).",
)
def summary(input_file: str, output: Optional[str]):
    """
    Generate a summary report for processed 1080 data.

    INPUT_FILE: Path to the input file (CSV, Excel, or JSON).
    """
    try:
        config = ProcessingConfig(skip_invalid=True)
        file_handler = FileHandler(config)
        processor = Processor1080(config)

        click.echo(f"Analyzing: {input_file}")
        raw_data = file_handler.read_file(input_file)
        result = processor.process_raw_data(raw_data)

        summary_data = processor.generate_summary(result)

        if output:
            with open(output, "w") as f:
                json.dump(summary_data, f, indent=2, default=str)
            click.echo(f"Summary written to: {output}")
        else:
            click.echo("\n" + "=" * 50)
            click.echo("1080 DATA PROCESSING SUMMARY")
            click.echo("=" * 50)

            click.echo("\nProcessing Results:")
            for key, value in summary_data["processing_summary"].items():
                click.echo(f"  {key}: {value}")

            click.echo("\nFinancial Totals:")
            for key, value in summary_data["financial_totals"].items():
                click.echo(f"  {key}: ${value:,.2f}")

            if summary_data["by_reporting_period"]:
                click.echo("\nBy Reporting Period:")
                for period, data in summary_data["by_reporting_period"].items():
                    click.echo(f"  {period}: {data['count']} records, ${data['amount']:,.2f}")

            if summary_data["by_record_type"]:
                click.echo("\nBy Record Type:")
                for rec_type, count in summary_data["by_record_type"].items():
                    click.echo(f"  {rec_type}: {count} records")

            if summary_data["error_summary"]["total_errors"] > 0:
                click.echo("\nError Summary:")
                click.echo(f"  Total errors: {summary_data['error_summary']['total_errors']}")
                for field, count in summary_data["error_summary"]["by_field"].items():
                    click.echo(f"    {field}: {count}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    required=True,
    help="Output file for aggregated data.",
)
@click.option(
    "-f", "--format",
    type=click.Choice(["csv", "xlsx", "json"]),
    default="csv",
    help="Output format.",
)
def aggregate(input_file: str, output: str, format: str):
    """
    Aggregate 1080 data by entity.

    Groups records by entity and calculates totals.

    INPUT_FILE: Path to the input file (CSV, Excel, or JSON).
    """
    try:
        config = ProcessingConfig(skip_invalid=True)
        file_handler = FileHandler(config)
        processor = Processor1080(config)

        click.echo(f"Reading: {input_file}")
        raw_data = file_handler.read_file(input_file)

        click.echo(f"Processing {len(raw_data)} records...")
        result = processor.process_raw_data(raw_data)

        click.echo("Aggregating by entity...")
        aggregated = processor.aggregate_by_entity(result.processed_records)

        # Convert to list for output
        agg_data = []
        for entity_id, data in aggregated.items():
            agg_data.append({
                "entity_id": data["entity_id"],
                "entity_name": data["entity_name"],
                "total_amount": float(data["total_amount"]),
                "total_secondary_amount": float(data["total_secondary_amount"]),
                "total_adjustment": float(data["total_adjustment"]),
                "record_count": data["record_count"],
            })

        # Write output
        import pandas as pd
        df = pd.DataFrame(agg_data)

        output_path = Path(output)
        if format == "csv":
            df.to_csv(output_path, index=False)
        elif format in ["xlsx", "excel"]:
            df.to_excel(output_path, index=False)
        else:
            with open(output_path, "w") as f:
                json.dump(agg_data, f, indent=2)

        click.echo(f"Aggregated data written to: {output_path}")
        click.echo(f"  Total entities: {len(aggregated)}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
