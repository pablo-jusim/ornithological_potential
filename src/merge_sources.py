"""
Merge sources script.

Merge eBird and iNaturalist datasets, associate observations to grid cells,
filter and clean records, count species per cell, and export final CSV.

Produces:
- ../data/interim/species_grid.csv
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

# output path
EBIRD_CSV_PATH = BASE_DIR.parent / 'data' / 'raw' / 'data_ebird.csv'
INAT_CSV_PATH = BASE_DIR.parent / 'data' / 'raw' / 'data_inat.csv'
GRID_GPKG_PATH = BASE_DIR.parent / 'data' / 'raw' / 'empty_local_grid.gpkg'
OUTPUT_CSV_PATH = BASE_DIR.parent / 'data' / 'interim' / 'species_grid.csv'

# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout
)


# -----------------------------------------------------------------------------
# Step 1: Load & merge cleaned CSVs
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
    for fp in (ebird_csv, inat_csv):
        if not fp.exists():
            logging.error("Input file not found: %s", fp)
            sys.exit(1)

    df_ebird = pd.read_csv(ebird_csv)
    df_inat = pd.read_csv(inat_csv)
    df_merged = pd.concat([df_ebird, df_inat], ignore_index=True)
    logging.info("Loaded and merged: %d total observations", len(df_merged))
    return df_merged


# -------------------------------------------------------------------------
# Step 2: Spatially associate each record to a grid cell
# -------------------------------------------------------------------------

def associate_grid(
    df: pd.DataFrame,
    grid_file: Path,
    cell_id_field: str = 'grid_id',
    epsg_code: int = 4326
) -> pd.DataFrame:
    """
    Associate each observation to its grid cell via spatial join.

    Args:
        df (pd.DataFrame): Merged observations.
        grid_file (Path): Path to GeoPackage with grid cells.
        cell_id_field (str): Name of the grid ID column.
        epsg_code (int): CRS code for points.

    Returns:
        pd.DataFrame: Observations with assigned cell IDs.
    """
    try:
        df_gridded = grid_association.main(
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


# -------------------------------------------------------------------------
# Step 3: Filter out rare species & clean names
# -------------------------------------------------------------------------

def filter_and_clean(
    df: pd.DataFrame,
    rare_threshold: int
) -> pd.DataFrame:
    """
    Remove rare species and erroneous scientific names.

    Args:
        df (pd.DataFrame): Gridded observations.
        rare_threshold (int): Max occurrences to classify a species as rare.

    Returns:
        pd.DataFrame: Cleaned observations.
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


# -------------------------------------------------------------------------
# Step 4: Count species per grid cell
# -------------------------------------------------------------------------

def count_species(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Count species per grid cell and return pivoted DataFrame.

    Args:
        df (pd.DataFrame): Cleaned observations.

    Returns:
        pd.DataFrame: Counts of each species per cell.
    """
    df_counts = utils.make_counts_dataframe(df)
    logging.info("Created species counts for %d cells", len(df_counts))
    return df_counts


# -------------------------------------------------------------------------
# Step 5: Export results to CSV
# -------------------------------------------------------------------------

def export_results(
    df: pd.DataFrame,
    output_csv: Path
) -> None:
    """
    Export the final counts DataFrame to CSV.

    Args:
        df (pd.DataFrame): Counts per cell.
        output_csv (Path): Destination CSV path.
    """
    if not output_csv.is_absolute():
        output_csv = Path(__file__).resolve().parent / output_csv

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    logging.info("Exported final counts to %s", output_csv)


# -----------------------------------------------------------------------------
# Main pipeline
# -----------------------------------------------------------------------------

def main(
    ebird_csv: Path = EBIRD_CSV_PATH,
    inat_csv: Path = INAT_CSV_PATH,
    grid_file: Path = GRID_GPKG_PATH,
    output_csv: Path = Path(OUTPUT_CSV_PATH),
    rare_threshold: int = 5
) -> None:
    """
    Execute the full merge → associate → filter → count → export pipeline.

    Args:
        ebird_csv     (Path): Cleaned eBird CSV path.
        inat_csv      (Path): Cleaned iNaturalist CSV path.
        grid_gpkg     (Path): Grid GeoPackage file.
        output_csv    (Path): Destination CSV for species counts.
        rare_threshold(int): Max occurrences to filter rare species.
    """
    merged = load_and_merge(ebird_csv, inat_csv)
    gridded = associate_grid(merged, grid_file)
    cleaned = filter_and_clean(gridded, rare_threshold)
    counts = count_species(cleaned)
    export_results(counts, output_csv)


if __name__ == '__main__':
    main()
