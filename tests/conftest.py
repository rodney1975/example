import os
import pytest

from src.data.parser import parse_csv, parse_directory
from src.api.server import app


SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "sample_data")
SAMPLE_CSV = os.path.join(SAMPLE_DATA_DIR, "sprint_session_001.csv")


@pytest.fixture
def sample_csv_path():
    return os.path.abspath(SAMPLE_CSV)


@pytest.fixture
def sample_data_dir():
    return os.path.abspath(SAMPLE_DATA_DIR)


@pytest.fixture
def sample_records(sample_csv_path):
    return parse_csv(sample_csv_path)


@pytest.fixture
def flask_client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
