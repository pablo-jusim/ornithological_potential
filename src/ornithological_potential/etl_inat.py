"""
iNaturalist Observations Preprocessing Script


This script performs validation and cleaning steps on
raw iNaturalist observations and produces a cleaned CSV
for downstream analysis.

Steps:
1. Load raw observations
2. Filter by positional accuracy
3. Normalize scientific names
4. Select relevant columns
5. Export cleaned data

Produces:
- ../data/raw/data_inat.csv

The output DataFrame will contain the following columns:
- common_name      : Common name of the species
- scientific_name  : Genus and species
- latitude         : Latitude of the observation
- longitude        : Longitude of the observation
- observed_on      : Date of the observation
"""

# %% Imports
import sys
import logging
from pathlib import Path
import pandas as pd

# Default paths
BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_INAT_PATH = BASE_DIR / "data" / "external" / "inat_obs.csv"
OUTPUT_INAT_PATH = BASE_DIR / "data" / "raw" / "data_inat.csv"

# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout
)


# -----------------------------------------------------------------------------
# Step 1: Load raw data
# -----------------------------------------------------------------------------

def load_raw_inat(filepath: Path) -> pd.DataFrame:
    """
    Load raw iNaturalist observation CSV into a DataFrame.

    Args:
        filepath (Path): Relative or absolute path to the raw CSV file.

    Returns:
        DataFrame: Raw observations.
    """
    if not filepath.is_absolute():
        filepath = Path(__file__).resolve().parent.parent / filepath

    if not filepath.exists():
        logging.error("File not found: %s", filepath)
        sys.exit(1)

    df = pd.read_csv(filepath)
    logging.info("Loaded %d raw iNaturalist records from %s",
                 len(df), filepath)
    return df


# -----------------------------------------------------------------------------
# Step 2: Filter by positional accuracy
# -----------------------------------------------------------------------------

def filter_by_accuracy(df: pd.DataFrame, max_accuracy: float) -> pd.DataFrame:
    """
    Remove observations with positional_accuracy >= max_accuracy.

    Args:
        df (DataFrame): Input observations.
        max_accuracy (float): Maximum allowed positional accuracy in meters.

    Returns:
        DataFrame: Filtered observations.
    """
    df_filtered = df[df['positional_accuracy'] < max_accuracy]
    logging.info(
        "Filtered by accuracy < %dm: %d records remain",
        max_accuracy,
        len(df_filtered)
    )
    return df_filtered


# -----------------------------------------------------------------------------
# Step 3: Normalize scientific names
# -----------------------------------------------------------------------------

def normalize_scientific_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure scientific_name column contains only genus and species.

    Args:
        df (DataFrame): Input with 'scientific_name' column.

    Returns:
        DataFrame: With truncated 'scientific_name'.
    """
    df = df.rename(columns={'scientific_name': 'scientific_name_sub'})
    df['scientific_name'] = df['scientific_name_sub'].apply(
        lambda x: ' '.join(x.split()[:2]) if isinstance(x, str) else x
    )
    logging.info("Normalized scientific names to genus and species")
    return df


# -----------------------------------------------------------------------------
# Step 4: Select relevant columns
# -----------------------------------------------------------------------------

def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the required columns.

    Args:
        df (DataFrame): Input observations.

    Returns:
        DataFrame: Columns ['common_name', 'scientific_name', 'latitude',
                            'longitude', 'observed_on']
    """
    cols = [
        'common_name',
        'scientific_name',
        'latitude',
        'longitude',
        'observed_on'
    ]
    df_selected = df[cols].copy()
    logging.info("Selected columns: %s", cols)
    return df_selected


# -----------------------------------------------------------------------------
# Step 5: Export cleaned data
# -----------------------------------------------------------------------------

def export_clean_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Export the cleaned DataFrame to CSV.

    Args:
        df (DataFrame): Cleaned observations.
        output_path (Path): Destination CSV file path.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info("Exported cleaned data to %s", output_path)


# -----------------------------------------------------------------------------
# Main pipeline
# -----------------------------------------------------------------------------

def main(
    input_csv: Path = INPUT_INAT_PATH,
    output_csv: Path = OUTPUT_INAT_PATH,
    max_accuracy: float = 2500.0
):
    """
    Run all preprocessing steps on iNaturalist data.

    Args:
        input_csv (Path): Path to raw CSV.
        output_csv (Path): Path to save cleaned CSV.
        max_accuracy (float): Max positional accuracy (meters).
    """

    df_raw = load_raw_inat(input_csv)
    df_acc = filter_by_accuracy(df_raw, max_accuracy)
    df_norm = normalize_scientific_names(df_acc)
    df_final = select_columns(df_norm)
    export_clean_data(df_final, output_csv)


# -----------------------------------------------------------------------------
# Script entry point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Preprocess raw iNaturalist observations into cleaned CSV"
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        type=Path,
        default=INPUT_INAT_PATH,
        help="Path to raw iNaturalist CSV file"
    )
    parser.add_argument(
        "output_csv",
        nargs="?",
        type=Path,
        default=OUTPUT_INAT_PATH,
        help=f"Destination CSV (default: {OUTPUT_INAT_PATH})"
    )
    parser.add_argument(
        "max_accuracy",
        nargs="?",
        type=float,
        default=2500,
        help="Maximum acceptable positional_accuracy in meters"
    )
    args = parser.parse_args()
    main(args.input_csv, args.output_csv, args.max_accuracy)