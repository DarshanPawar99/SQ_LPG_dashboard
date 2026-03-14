"""
data_loader.py

Loads the LPG Stock Tracker workbook with 2 sheets:

- Master Vendor Data
- Master Client Data

Business rules:
- Filter out vendors where GAIL/PNG at Vendor == 'Yes'
- Join vendor and client sheets using Unique Vendor ID
- Final output grain = one row per client + vendor
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import (
    CANONICAL_CLIENT,
    CANONICAL_CONTINUITY,
    CANONICAL_DAYS_OF_STOCK,
    CANONICAL_GAIL_PNG,
    CANONICAL_LAST_UPDATED,
    CANONICAL_PAX,
    CANONICAL_REGION,
    CANONICAL_VENDOR,
    CANONICAL_VENDOR_ID,
    CLIENT_SHEET_NAME,
    DATA_FILE_PATH,
    EXCLUDED_GAIL_PNG_VALUES,
    EXCLUDE_GAIL_PNG_YES,
    VENDOR_SHEET_NAME,
)
from logger import setup_logger

logger = setup_logger(__name__)


# -------------------------------------------------------------------
# EXACT COLUMN NAMES FROM YOUR FILE
# -------------------------------------------------------------------
VENDOR_EXACT_COLUMNS = {
    CANONICAL_VENDOR_ID: "Unique Vendor ID",
    CANONICAL_REGION: "Region",
    CANONICAL_VENDOR: "Vendor Name",
    CANONICAL_DAYS_OF_STOCK: "Days of Stock",
    CANONICAL_LAST_UPDATED: "Last Updated Date",
    CANONICAL_GAIL_PNG: "GAIL/PNG at Vendor",
    CANONICAL_CONTINUITY: "Electrical Equipment Availability",
}

CLIENT_EXACT_COLUMNS = {
    CANONICAL_VENDOR_ID: "Unique Vendor ID",
    CANONICAL_VENDOR: "Vendor Name",
    CANONICAL_CLIENT: "Client Name",
    CANONICAL_PAX: "Total Pax Served through SQ (Only Offsite)",
}


# -------------------------------------------------------------------
# LOAD WORKBOOK
# -------------------------------------------------------------------
def load_raw_workbook(file_path: str | Path = DATA_FILE_PATH) -> tuple[pd.DataFrame, pd.DataFrame]:
    path = Path(file_path)
    if not path.exists():
        logger.error("Dataset file not found: %s", path)
        raise FileNotFoundError(f"Dataset file not found: {path}")

    logger.info("Loading workbook from %s", path)
    vendor_df = pd.read_excel(path, sheet_name=VENDOR_SHEET_NAME)
    client_df = pd.read_excel(path, sheet_name=CLIENT_SHEET_NAME)
    logger.info("Workbook loaded: vendor rows=%s, client rows=%s", len(vendor_df), len(client_df))

    return vendor_df, client_df


# -------------------------------------------------------------------
# RENAME TO CANONICAL COLUMNS
# -------------------------------------------------------------------
def standardize_vendor_columns(df: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in VENDOR_EXACT_COLUMNS.values() if col not in df.columns]
    if missing:
        raise ValueError(f"Missing vendor sheet columns: {missing}")

    vendor_df = df.rename(columns={v: k for k, v in VENDOR_EXACT_COLUMNS.items()}).copy()

    keep_cols = [
        CANONICAL_VENDOR_ID,
        CANONICAL_REGION,
        CANONICAL_VENDOR,
        CANONICAL_DAYS_OF_STOCK,
        CANONICAL_LAST_UPDATED,
        CANONICAL_GAIL_PNG,
        CANONICAL_CONTINUITY,
    ]
    return vendor_df[keep_cols]


def standardize_client_columns(df: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in CLIENT_EXACT_COLUMNS.values() if col not in df.columns]
    if missing:
        raise ValueError(f"Missing client sheet columns: {missing}")

    client_df = df.rename(columns={v: k for k, v in CLIENT_EXACT_COLUMNS.items()}).copy()

    keep_cols = [
        CANONICAL_VENDOR_ID,
        CANONICAL_VENDOR,
        CANONICAL_CLIENT,
        CANONICAL_PAX,
    ]
    return client_df[keep_cols]


# -------------------------------------------------------------------
# CLEANING
# -------------------------------------------------------------------
def clean_vendor_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    for col in [
        CANONICAL_VENDOR_ID,
        CANONICAL_REGION,
        CANONICAL_VENDOR,
        CANONICAL_GAIL_PNG,
        CANONICAL_CONTINUITY,
    ]:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].astype("string").fillna("").str.strip()

    cleaned[CANONICAL_DAYS_OF_STOCK] = pd.to_numeric(
        cleaned[CANONICAL_DAYS_OF_STOCK],
        errors="coerce",
    ).fillna(0)

    cleaned[CANONICAL_LAST_UPDATED] = pd.to_datetime(
        cleaned[CANONICAL_LAST_UPDATED],
        errors="coerce",
    )

    cleaned = cleaned.dropna(subset=[CANONICAL_LAST_UPDATED])
    cleaned = cleaned[cleaned[CANONICAL_VENDOR_ID].astype(str).str.strip() != ""]
    cleaned = cleaned[cleaned[CANONICAL_VENDOR].astype(str).str.strip() != ""]
    cleaned = cleaned[cleaned[CANONICAL_REGION].astype(str).str.strip() != ""]

    return cleaned.reset_index(drop=True)


def clean_client_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    for col in [CANONICAL_VENDOR_ID, CANONICAL_VENDOR, CANONICAL_CLIENT]:
        cleaned[col] = cleaned[col].astype("string").fillna("").str.strip()

    cleaned[CANONICAL_PAX] = pd.to_numeric(
        cleaned[CANONICAL_PAX],
        errors="coerce",
    ).fillna(0)

    cleaned = cleaned[cleaned[CANONICAL_VENDOR_ID].astype(str).str.strip() != ""]
    cleaned = cleaned[cleaned[CANONICAL_CLIENT].astype(str).str.strip() != ""]

    return cleaned.reset_index(drop=True)


# -------------------------------------------------------------------
# FILTER RULE
# -------------------------------------------------------------------
def filter_out_gail_png_yes(vendor_df: pd.DataFrame) -> pd.DataFrame:
    if not EXCLUDE_GAIL_PNG_YES:
        return vendor_df.copy()

    normalized = (
        vendor_df[CANONICAL_GAIL_PNG]
        .astype("string")
        .fillna("")
        .str.strip()
        .str.lower()
    )

    filtered = vendor_df[~normalized.isin(EXCLUDED_GAIL_PNG_VALUES)].copy()
    return filtered.reset_index(drop=True)


# -------------------------------------------------------------------
# MERGE
# -------------------------------------------------------------------
def merge_client_vendor_data(client_df: pd.DataFrame, vendor_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge client rows to vendor rows using vendor_id.

    Final grain:
    one row = one client + one vendor
    """
    merged = client_df.merge(
        vendor_df,
        on=CANONICAL_VENDOR_ID,
        how="inner",
        suffixes=("_client", "_vendor"),
    )

    # Prefer vendor region because client location is mostly blank in your file
    merged[CANONICAL_REGION] = merged[f"{CANONICAL_REGION}"]

    # Prefer vendor name from vendor sheet
    if f"{CANONICAL_VENDOR}_vendor" in merged.columns:
        merged[CANONICAL_VENDOR] = merged[f"{CANONICAL_VENDOR}_vendor"]
    elif f"{CANONICAL_VENDOR}_client" in merged.columns:
        merged[CANONICAL_VENDOR] = merged[f"{CANONICAL_VENDOR}_client"]

    final_cols = [
        CANONICAL_VENDOR_ID,
        CANONICAL_VENDOR,
        CANONICAL_CLIENT,
        CANONICAL_REGION,
        CANONICAL_PAX,
        CANONICAL_DAYS_OF_STOCK,
        CANONICAL_LAST_UPDATED,
        CANONICAL_GAIL_PNG,
        CANONICAL_CONTINUITY,
    ]

    return merged[final_cols].reset_index(drop=True)


# -------------------------------------------------------------------
# PUBLIC LOADER
# -------------------------------------------------------------------
def load_dashboard_data(file_path: str | Path = DATA_FILE_PATH) -> pd.DataFrame:
    raw_vendor_df, raw_client_df = load_raw_workbook(file_path=file_path)

    vendor_df = standardize_vendor_columns(raw_vendor_df)
    client_df = standardize_client_columns(raw_client_df)

    vendor_df = clean_vendor_dataframe(vendor_df)
    client_df = clean_client_dataframe(client_df)

    vendor_df = filter_out_gail_png_yes(vendor_df)

    merged_df = merge_client_vendor_data(client_df, vendor_df)
    logger.info("Dashboard data prepared with %s merged rows", len(merged_df))
    return merged_df


if __name__ == "__main__":
    try:
        df = load_dashboard_data()
        print("Dashboard data loaded successfully")
        print(df.head())
        print(f"Rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")
    except Exception as exc:
        print(f"Error loading dashboard data: {exc}")