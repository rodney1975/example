import os
from pathlib import Path

import pandas as pd

from src.data.models import SprintRecord

EXPECTED_COLUMNS = [
    "Rep",
    "Timestamp (s)",
    "Position (m)",
    "Velocity (m/s)",
    "Acceleration (m/s²)",
    "Force (N)",
    "Power (W)",
    "Stroke Phase",
]

UNICODE_MINUS = "\u2212"


def _normalize_minus_signs(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].str.replace(UNICODE_MINUS, "-", regex=False)
    return df


def _validate_columns(df: pd.DataFrame) -> None:
    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")


def parse_csv(filepath: str) -> list[SprintRecord]:
    df = pd.read_csv(filepath, dtype=str)
    _validate_columns(df)
    df = _normalize_minus_signs(df)

    df["Rep"] = df["Rep"].astype(int)
    df["Timestamp (s)"] = df["Timestamp (s)"].astype(float)
    df["Position (m)"] = df["Position (m)"].astype(float)
    df["Velocity (m/s)"] = df["Velocity (m/s)"].astype(float)
    df["Acceleration (m/s²)"] = df["Acceleration (m/s²)"].astype(float)
    df["Force (N)"] = df["Force (N)"].astype(float)
    df["Power (W)"] = df["Power (W)"].astype(float)
    df["Stroke Phase"] = df["Stroke Phase"].str.strip()

    records: list[SprintRecord] = []
    for _, row in df.iterrows():
        records.append(
            SprintRecord(
                rep=int(row["Rep"]),
                timestamp=float(row["Timestamp (s)"]),
                position=float(row["Position (m)"]),
                velocity=float(row["Velocity (m/s)"]),
                acceleration=float(row["Acceleration (m/s²)"]),
                force=float(row["Force (N)"]),
                power=float(row["Power (W)"]),
                stroke_phase=row["Stroke Phase"],
            )
        )
    return records


def parse_directory(dirpath: str) -> dict[str, list[SprintRecord]]:
    result: dict[str, list[SprintRecord]] = {}
    dirpath_obj = Path(dirpath)
    for csv_file in sorted(dirpath_obj.glob("*.csv")):
        result[csv_file.name] = parse_csv(str(csv_file))
    return result
