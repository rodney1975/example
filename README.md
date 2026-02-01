# 1080 Data Processor

A Python application for processing, validating, and exporting 1080 data files. This tool handles data in CSV, Excel, and JSON formats with comprehensive validation and aggregation capabilities.

## Features

- **Multi-format Support**: Read and write CSV, Excel (.xlsx), and JSON files
- **Data Validation**: Validate entity information, financial amounts, addresses, and custom rules
- **Batch Processing**: Process large datasets efficiently
- **Aggregation**: Aggregate records by entity with calculated totals
- **Flexible Configuration**: Customize validation rules and processing behavior
- **CLI Interface**: Easy-to-use command-line interface
- **Detailed Reporting**: Generate processing summaries and error reports

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd example

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

## Quick Start

### Process a Data File

```bash
# Basic processing
processor-1080 process data/samples/sample_1080_data.csv -o output/processed.csv

# Process with JSON output
processor-1080 process data/samples/sample_1080_data.csv -o output/processed.json -f json

# Validate only (no processing)
processor-1080 process data/samples/sample_1080_data.csv --validate-only
```

### Preview Data

```bash
# Preview first 10 records
processor-1080 preview data/samples/sample_1080_data.csv

# Preview with custom limit
processor-1080 preview data/samples/sample_1080_data.csv -n 20
```

### Generate Summary

```bash
# Display summary to console
processor-1080 summary data/samples/sample_1080_data.csv

# Save summary to file
processor-1080 summary data/samples/sample_1080_data.csv -o summary.json
```

### Batch Processing

```bash
# Full batch processing with all output files
processor-1080 batch data/samples/sample_1080_data.csv -o output/

# This generates:
#   - output/processed_1080_YYYYMMDD_HHMMSS.csv
#   - output/processed_1080_YYYYMMDD_HHMMSS_summary.json
#   - output/processed_1080_YYYYMMDD_HHMMSS_errors.csv (if errors exist)
```

### Aggregate by Entity

```bash
# Aggregate records by entity
processor-1080 aggregate data/samples/sample_1080_data.csv -o aggregated.csv
```

## CLI Options

### Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version information |
| `--help` | Show help message |

### Process Command Options

| Option | Description |
|--------|-------------|
| `-o, --output` | Output file path |
| `-f, --format` | Output format (csv, xlsx, json) |
| `--validate-only` | Only validate, don't process |
| `--skip-invalid` | Skip invalid records |
| `--allow-negative` | Allow negative amounts |
| `--require-address` | Require complete address |
| `-v, --verbose` | Enable verbose logging |
| `-q, --quiet` | Suppress non-error output |

## Data Format

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `entity_name` | Name of the entity | "Acme Corporation" |
| `entity_id` | Entity identification number | "12-3456789" |
| `amount` | Primary amount | 15000.00 |
| `transaction_date` | Date of transaction | "2024-01-15" |
| `reporting_period` | Reporting period | "2024-Q1" |

### Optional Fields

| Field | Description | Example |
|-------|-------------|---------|
| `record_id` | Unique record identifier | "REC-001" |
| `record_type` | Type (standard, amended, corrected, void) | "standard" |
| `entity_address` | Street address | "123 Main Street" |
| `entity_city` | City | "New York" |
| `entity_state` | State code (2 letters) | "NY" |
| `entity_zip` | ZIP code | "10001" |
| `secondary_amount` | Secondary amount | 500.00 |
| `adjustment_amount` | Adjustment amount | -100.00 |
| `notes` | Additional notes | "Quarterly payment" |

## Python API

```python
from processor_1080 import Processor1080, FileHandler, ProcessingConfig

# Create configuration
config = ProcessingConfig(
    allow_negative_amounts=True,
    skip_invalid=True,
    output_format="csv"
)

# Initialize components
processor = Processor1080(config)
file_handler = FileHandler(config)

# Read data
raw_data = file_handler.read_file("data/input.csv")

# Process data
result = processor.process_raw_data(raw_data)

# Check results
print(f"Processed: {result.successful} / {result.total_records}")
print(f"Errors: {result.failed}")

# Write output
file_handler.write_file(result.processed_records, "output/processed.csv")

# Generate summary
summary = processor.generate_summary(result)
print(summary)

# Aggregate by entity
aggregated = processor.aggregate_by_entity(result.processed_records)
for entity_id, data in aggregated.items():
    print(f"{data['entity_name']}: ${data['total_amount']}")
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=processor_1080 --cov-report=html
```

## Project Structure

```
example/
├── processor_1080/
│   ├── __init__.py       # Package initialization
│   ├── models.py         # Data models (Record1080, ProcessingResult, etc.)
│   ├── processor.py      # Core processing logic
│   ├── file_handler.py   # File I/O operations
│   └── cli.py            # Command-line interface
├── data/
│   └── samples/          # Sample data files
├── tests/
│   └── test_processor.py # Unit tests
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project configuration
└── README.md             # This file
```

## License

MIT License
