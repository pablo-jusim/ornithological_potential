# Ornithological Potential
# Author: Pablo Jusim

# eBird Observations Preprocessing Script

"""
This script loads raw eBird observation data, selects and renames
relevant columns, and exports a cleaned CSV ready for downstream analysis.

Steps:
1. Load raw observations
2. Select and rename columns to match iNaturalist format
3. Export cleaned data

Produces:
- ../data/raw/data_ebird.csv

The output DataFrame will contain the following columns:
- common_name   : Common name of the species
- scientific_name: Scientific name of the species
- latitude      : Latitude of the observation
- longitude     : Longitude of the observation
- observed_on   : Date of the observation
"""

# %% Imports
import sys
import logging
from pathlib import Path
import pandas as pd

# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout
)


# -----------------------------------------------------------------------------
# Step 1: Load raw eBird data
# -----------------------------------------------------------------------------

def load_raw_ebird(filepath: Path) -> pd.DataFrame:
    """
    Load raw eBird observation text file into a DataFrame.

    Args:
        filepath (Path): Relative or absolute path to the raw .txt file.

    Returns:
        DataFrame: Raw observations.
    """
    # Resolve relative paths relative to script location
    if not filepath.is_absolute():
        root_dir = Path(__file__).resolve().parent
        filepath = root_dir / filepath

    if not filepath.exists():
        logging.error("File not found: %s", filepath)
        sys.exit(1)

    df = pd.read_csv(filepath, sep='\t')
    logging.info("Loaded %d raw eBird records from %s", len(df), filepath)
    return df


# -----------------------------------------------------------------------------
# Step 2: Select and rename columns
# -----------------------------------------------------------------------------

def select_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only relevant columns and rename them to standard format.

    Args:
        df (DataFrame): Raw eBird DataFrame.

    Returns:
        DataFrame: Cleaned DataFrame with standardized column names.
    """
    mapping = {
        'COMMON NAME': 'common_name',
        'SCIENTIFIC NAME': 'scientific_name',
        'LATITUDE': 'latitude',
        'LONGITUDE': 'longitude',
        'OBSERVATION DATE': 'observed_on'
    }
    df_selected = df[list(mapping.keys())].rename(columns=mapping)
    logging.info("Selected and renamed columns: %s", list(mapping.values()))
    return df_selected


# -----------------------------------------------------------------------------
# Step 3: Export cleaned data
# -----------------------------------------------------------------------------

def export_clean_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Export the cleaned DataFrame to CSV.

    Args:
        df (DataFrame): Cleaned observations.
        output_path (Path): Destination CSV file path.
    """
    # Resolve relative path
    if not output_path.is_absolute():
        root_dir = Path(__file__).resolve().parent.parent
        output_path = root_dir / output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info("Exported cleaned data to %s", output_path)


# -----------------------------------------------------------------------------
# Main pipeline
# -----------------------------------------------------------------------------

def main(raw_path: Path):
    """
    Main function to execute the preprocessing steps on eBird data.

    Args:
        raw_path (Path): Path to the raw eBird TXT file.
    """
    output_path = Path('data/raw/data_ebird.csv')

    df_raw = load_raw_ebird(raw_path)
    df_clean = select_and_rename_columns(df_raw)
    export_clean_data(df_clean, output_path)
