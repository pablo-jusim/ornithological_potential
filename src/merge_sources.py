# Potencial Ornitológico Fueguino
# Author: Pablo Jusim

"""
Merge eBird and iNaturalist datasets, associate observations to grid cells,
filter and clean records, count species per cell, and export final CSV.

Produces:
- ../data/interim/grilla_tdf_spp.csv
"""

# %% Imports
import sys
import logging
from pathlib import Path
import pandas as pd
from pyogrio.errors import DataSourceError

# Add project `src` directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR.parent / 'src'))

import grid_association
import utils

# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------

def load_and_merge(
    ebird_csv: Path,
    inat_csv: Path
        ) -> pd.DataFrame:
    """
    Load cleaned CSVs from eBird and iNaturalist and concatenate them.

    Args:
        ebird_csv (Path): Path to cleaned eBird CSV.
        inat_csv (Path): Path to cleaned iNaturalist CSV.

    Returns:
        DataFrame: Merged observations.
    """
    try:
        # Load eBird and iNaturalist data from CSV files
        df_ebird = pd.read_csv(ebird_csv)
        df_inat = pd.read_csv(inat_csv)
    except FileNotFoundError as e:
        # Log error and exit if either file is not found
        logging.error("Input file not found: %s", e.filename)
        sys.exit(1)
    df_merged = pd.concat([df_ebird, df_inat], ignore_index=True)
    logging.info("Loaded and merged: %d total observations", len(df_merged))
    return df_merged


def associate_grid(
    df: pd.DataFrame,
    grid_file: Path,
    cell_id_field: str = 'grid_id',
    epsg_code: int = 4326
) -> pd.DataFrame:
    """
    Associate each observation to its grid cell via spatial join.

    Args:
        df (DataFrame): Merged observations.
        grid_file (Path): Path to GeoPackage with grid cells.
        cell_id_field (str): Name of the grid ID column.
        epsg_code (int): CRS code for points.

    Returns:
        DataFrame: Observations with assigned cell IDs.
    """
    try:
        df_gridded = grid_association.assign_grid_cell_ids(
            grid_file=grid_file,
            observations=df,
            cell_id_field=cell_id_field,
            epsg_code=epsg_code
        )
    except DataSourceError:
        logging.error("Failed to load grid file: %s", grid_file)
        sys.exit(1)
    logging.info("Assigned grid cells: %d records", len(df_gridded))
    return df_gridded


def filter_and_clean(
    df: pd.DataFrame,
    rare_threshold: int
) -> pd.DataFrame:
    """
    Remove rare species and erroneous scientific names.

    Args:
        df (DataFrame): Gridded observations.
        rare_threshold (int): Max occurrences to classify a species as rare.

    Returns:
        DataFrame: Cleaned observations.
    """
    df_no_rare = utils.remove_rare_species(df, threshold=rare_threshold)
    logging.info("Filtered rare species (<=%d): %d records", rare_threshold,
                 len(df_no_rare))
    df_no_rare['scientific_name'] = df_no_rare['scientific_name'].str.strip()
    df_no_slash = df_no_rare[~df_no_rare['scientific_name']
                             .str.contains(r'[\\/]', regex=True)]
    df_clean = df_no_slash[~df_no_slash['scientific_name']
                           .str.contains(r'(?i)\b(?:sp\.|spp\.)', regex=True)]
    logging.info("Removed erroneous names: %d records", len(df_clean))
    return df_clean


def count_species(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Count species per grid cell and return pivoted DataFrame.

    Args:
        df (DataFrame): Cleaned observations.

    Returns:
        DataFrame: Counts of each species per cell.
    """
    df_counts = utils.make_counts_dataframe(df)
    logging.info("Created species counts for %d cells", len(df_counts))
    return df_counts


def export_results(
    df: pd.DataFrame,
    output_csv: Path
) -> None:
    """
    Export the final counts DataFrame to CSV.

    Args:
        df (DataFrame): Counts per cell.
        output_csv (Path): Destination CSV path.
    """
    if not output_csv.is_absolute():
        root_dir = Path(__file__).resolve().parent.parent
        output_csv = root_dir / output_csv
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    logging.info("Exported final counts to %s", output_csv)


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def main(
    ebird_csv: Path = Path('data/raw/data_ebird.csv'),
    inat_csv: Path = Path('data/raw/data_inat.csv'),
    grid_file: Path = Path('data/raw/grilla_tdf_vacia.gpkg'),
    output_csv: Path = Path('data/interim/grilla_tdf_spp.csv'),
    rare_threshold: int = 5
) -> None:
    """
    Execute the merge, associate, filter, count, and export pipeline.
    """
    df_merged = load_and_merge(ebird_csv, inat_csv)
    df_gridded = associate_grid(df_merged, grid_file)
    df_clean = filter_and_clean(df_gridded, rare_threshold)
    df_counts = count_species(df_clean)
    export_results(df_counts, output_csv)


if __name__ == '__main__':
    main()
