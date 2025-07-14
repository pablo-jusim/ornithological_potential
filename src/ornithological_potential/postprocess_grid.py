"""
Post-processing script for clustered grid data.

This script computes weighted richness scores for each grid cell,
normalizes the scores within each cluster, merges the scores back
into the spatial grid, and exports the enriched grid to a GeoPackage.

Steps:
1. Load clustered grid and species counts
2. Compute weighted richness and normalized score per cluster
3. Merge scores back into spatial grid
4. Export enriched grid as GeoPackage

Produces:
- ../data/processed/grilla_riqueza.gpkg
"""
# %% Imports
import sys
import logging
from pathlib import Path
import pandas as pd
import geopandas as gpd
from pyogrio.errors import DataSourceError

# Add project `src` directory to Python path
BASE_DIR = Path(__file__).resolve().parents[2]
GRID_PATH = BASE_DIR / 'data' / 'interim' / 'clusters_grid.gpkg'
COUNTS_PATH = BASE_DIR / 'data' / 'interim' / 'species_grid.csv'
OUTPUT_PATH = BASE_DIR / 'data' / 'processed' / 'richness_grid.gpkg'

# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout
)


# -----------------------------------------------------------------------------
# Step 1: Load data
# -----------------------------------------------------------------------------

def load_data(
    grid_path: Path,
    layer: str,
    counts_path: Path
) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """
    Load spatial grid and species counts from the given paths.

    Args:
        grid_path (Path): Path to clustered grid GeoPackage.
        layer (str): Name of the layer inside the GeoPackage to read.
        counts_path (Path): Path to species counts CSV.

    Returns:
        tuple: (grid GeoDataFrame, counts DataFrame)
    """
    # Resolve relative to project
    project_root = BASE_DIR
    counts_fp = (
        project_root / counts_path
        if not counts_path.is_absolute()
        else counts_path
                 )

    try:
        grid_gdf = gpd.read_file(grid_path, layer=layer)
        logging.info("Loaded grid: %s", grid_path)
    except DataSourceError:
        logging.error("Grid file not found: %s", grid_path)
        sys.exit(1)

    if not counts_fp.exists():
        logging.error("Counts file not found: %s", counts_fp)
        sys.exit(1)

    counts_df = pd.read_csv(counts_fp)
    logging.info("Loaded counts: %d rows", len(counts_df))

    return grid_gdf, counts_df


# -----------------------------------------------------------------------------
# Step 2: Compute weighted richness and normalized score
# -----------------------------------------------------------------------------

def compute_scores(
    counts_df: pd.DataFrame,
    priority_species: list[str],
    priority_weight: int
) -> pd.DataFrame:
    """
    Calculate weighted richness and normalized score per cluster cell.

    Args:
        counts_df (DataFrame): Index=grid_id, columns=species counts.
        priority_species (list): Species to weight more.
        priority_weight (int): Weight for priority species.

    Returns:
        DataFrame: DataFrame with columns ['grid_id','score_riqueza']
    """
    if priority_species is None:
        priority_species = []
    # set index
    reg_idx = counts_df.set_index('grid_id')

    # normalize by max per species
    max_per_sp = reg_idx.max(axis=0)
    prop_df = reg_idx.div(max_per_sp, axis=1)

    # assign weights
    weights = pd.Series(1.0, index=reg_idx.columns)
    for sp in priority_species:
        if sp in weights.index:
            weights[sp] = float(priority_weight)
    weighted = prop_df.multiply(weights, axis=1)

    # Sum across species to get weighted richness
    richness = weighted.sum(axis=1)
    score_df = richness.to_frame('weighted_richness')
    score_df.reset_index(inplace=True)

    return score_df


# -----------------------------------------------------------------------------
# Step 3: Merge scores back into grid
# -----------------------------------------------------------------------------

def merge_scores(
    grid_gdf: gpd.GeoDataFrame,
    score_df: pd.DataFrame
) -> gpd.GeoDataFrame:
    """
    Merge weighted richness and compute relative score per cluster.

    Args:
        grid_gdf (GeoDataFrame): Original grid with 'grid_id'
        and 'GaussianMixture'.
        score_df (pd.DataFrame): DataFrame with 'grid_id'
        and 'weighted_richness' columns.

    Returns:
        GeoDataFrame: grid with new 'richness_score' column.
    """
    df_calc = grid_gdf[['grid_id', 'GaussianMixture']].copy()
    df_calc = df_calc[df_calc['GaussianMixture'].notna()]
    df_calc = df_calc.rename(columns={'GaussianMixture': 'cluster'})

    # merge richness
    calc = df_calc.merge(score_df, on='grid_id', how='left')

    # normalize per cluster
    calc['richness_score'] = (
        calc.groupby('cluster')['weighted_richness']
            .transform(lambda x: x / x.max())
    )

    # assign back to GeoDataFrame
    result = grid_gdf.merge(
        calc[['grid_id', 'richness_score']],
        on='grid_id', how='left'
    )
    logging.info("Merged scores into grid")
    return result


# -----------------------------------------------------------------------------
# Step 4: Export enriched grid
# -----------------------------------------------------------------------------

def export_grid(
    enriched_gdf: gpd.GeoDataFrame,
    output_path: Path
) -> None:
    """
    Save enriched grid to GeoPackage.
    """
    project_root = BASE_DIR.parent
    out_fp = (
        project_root / output_path
        if not output_path.is_absolute()
        else output_path
        )
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    enriched_gdf.to_file(out_fp, driver='GPKG', layer='grilla_clusters')
    logging.info("Exported enriched grid to %s", out_fp)


# -----------------------------------------------------------------------------
# Script entry point
# -----------------------------------------------------------------------------

def main(
    grid_path=GRID_PATH,
    layer='clusters_grid',
    counts_path=COUNTS_PATH,
    export_path=OUTPUT_PATH,
    priority_species: list[str] = None,
    priority_weight: int = 1
) -> None:
    """
    Execute post-processing: compute scores, export grid, and generate map.
    """

    grid_gdf, counts_df = load_data(grid_path, layer, counts_path)
    score_df = compute_scores(counts_df, priority_species, priority_weight)
    enriched = merge_scores(grid_gdf, score_df)
    export_grid(enriched, export_path)


if __name__ == '__main__':
    main()
