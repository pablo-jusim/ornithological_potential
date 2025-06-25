# Potencial Ornitológico Fueguino
# Author: Pablo Jusim

"""
Post-processing pipeline for cluster richness.

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
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR.parent / 'src'))

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
    counts_path: Path
) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """
    Load spatial grid and species counts.

    Args:
        grid_path (Path): Path to clustered grid GeoPackage.
        counts_path (Path): Path to species counts CSV.

    Returns:
        tuple: (grid GeoDataFrame, counts DataFrame)
    """
    # Resolve relative to project
    project_root = BASE_DIR
    grid_fp = (
        project_root / grid_path
        if not grid_path.is_absolute()
        else grid_path
               )
    counts_fp = (
        project_root / counts_path
        if not counts_path.is_absolute()
        else counts_path
                 )

    try:
        grid_gdf = gpd.read_file(grid_fp)
        logging.info("Loaded grid: %s", grid_fp)
    except DataSourceError:
        logging.error("Grid file not found: %s", grid_fp)
        sys.exit(1)

    if not counts_fp.exists():
        logging.error("Counts file not found: %s", counts_fp)
        sys.exit(1)

    counts_df = pd.read_csv(counts_fp)
    logging.info("Loaded counts: %d rows", len(counts_df))

    return grid_gdf, counts_df


# -----------------------------------------------------------------------------
# Step 2: Compute weighted richness and score
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

    # compute richness and score per cluster
    richness = weighted.sum(axis=1)
    # get cluster assignments from reg_idx if present
    # assume cluster column in original grid merged later
    score_df = richness.to_frame('riqueza_ponderada')
    # will compute normalized by cluster after merging
    return score_df.reset_index()


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
        score_df (DataFrame): DataFrame with 'grid_id' and 'riqueza_ponderada'.

    Returns:
        GeoDataFrame: grid with new 'score_riqueza' column.
    """
    df_calc = grid_gdf[['grid_id', 'GaussianMixture']].copy()
    df_calc = df_calc[df_calc['GaussianMixture'].notna()]
    df_calc = df_calc.rename(columns={'GaussianMixture': 'cluster'})

    # merge richness
    calc = df_calc.merge(score_df, on='grid_id', how='left')

    # normalize per cluster
    calc['score_riqueza'] = (
        calc.groupby('cluster')['riqueza_ponderada']
            .transform(lambda x: x / x.max())
    )

    # assign back to GeoDataFrame
    result = grid_gdf.merge(
        calc[['grid_id', 'score_riqueza']],
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
# Main entry point
# -----------------------------------------------------------------------------

def main(
    grid_path: Path = Path('../data/processed/grilla_tdf_clusters.gpkg'),
    counts_path: Path = Path('../data/interim/grilla_tdf_spp.csv'),
    enriched_path: Path = Path('../data/processed/grilla_riqueza.gpkg'),
    priority_species: list[str] = None,
    priority_weight: int = 1
) -> None:
    """
    Execute post-processing: compute scores, export grid, and generate map.
    """

    grid_gdf, counts_df = load_data(grid_path, counts_path)
    score_df = compute_scores(counts_df, priority_species, priority_weight)
    enriched = merge_scores(grid_gdf, score_df)
    export_grid(enriched, enriched_path)


if __name__ == '__main__':
    main()
