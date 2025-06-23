# Potencial Ornitológico Fueguino
# Author: Pablo Jusim

# iNaturalist Observations Preprocessing Script


"""
This script performs validation and cleaning steps on
raw iNaturalist observations
and produces a final pandas DataFrame where each row corresponds to
a single observation.

Steps:
1. Load raw observations
2. Filter by positional accuracy
3. Normalize scientific names
4. Select relevant columns
5. Export cleaned data

Produces:
- ../data/raw/data_inat.csv

The output DataFrame will contain the following **columns**:
- obs_id        : Unique identifier of the observation
- cell_id       : ID of the grid cell where the observation falls
- species       : Common or scientific name of the observed species
- family        : Taxonomic family
- order         : Taxonomic order
- observed_date : Date of the observation
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
    # Si es una ruta relativa, convertirla en absoluta basada en el proyecto
    if not filepath.is_absolute():
        root_dir = Path(__file__).resolve().parent
        filepath = root_dir / filepath

    if not filepath.exists():
        logging.error("File not found: %s", filepath)
        sys.exit(1)

    df = pd.read_csv(filepath)
    logging.info("Loaded %d raw records from %s", len(df), filepath)
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
        df (DataFrame): Input DataFrame with 'scientific_name' column.

    Returns:
        DataFrame: DataFrame with new 'scientific_name' and backup column.
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
    Keep only the required columns for output.

    Args:
        df (DataFrame): Input DataFrame.

    Returns:
        DataFrame: Columns ['common_name', 'scientific_name', 'latitude',
        'longitude', 'observed_on']
    """
    cols = ['common_name', 'scientific_name', 'latitude', 'longitude',
            'observed_on']
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
    Main function to execute the preprocessing steps on iNaturlist data.

    Args:
        raw_path (Path): Path to the raw iNat CSV file.
    """
    output_path = Path('data/raw/data_inat.csv')

    df_raw = load_raw_inat(raw_path)
    df_acc = filter_by_accuracy(df_raw, max_accuracy=2500)
    df_norm = normalize_scientific_names(df_acc)
    df_final = select_columns(df_norm)
    export_clean_data(df_final, output_path)
