"""
Utility Functions for Ornithological Potential
==============================================

This module provides reusable functions to support the ornithological
pipeline, including tasks for data cleaning, grid preparation, clustering,
and mapping.

Main functionalities:
----------------------
- **Rare species filtering**: Identify and remove species with low occurrence.
- **Species counts per cell**: Generate pivot tables of species richness
  per grid cell.
- **Merge model results**: Attach clustering results back to spatial grids.
- **Cluster selection utilities**: Evaluate and select the best number
  of clusters.
- **Mapping helpers**: Format cluster colour palettes and opacities
  for interactive maps.

Functions:
----------
- `list_rare_species(df, threshold)`: Return names of species below threshold.
- `remove_rare_species(df, threshold)`: Filter out rare species from dataset.
- `make_counts_dataframe(df)`: Pivot species counts per grid cell.
- `merge_model_results(grid_gdf, cell_ids, cluster_labels, model_name)`:
   Merge clusters into GeoDataFrame.
- `select_best_k(...)`: Determine optimal k for clustering using BIC, AIC
   or silhouette.
- `categorise_opacity(score)`: Map scores to opacity levels for visualisation.
- `generate_cluster_colors(num_clusters)`: Generate colour palettes
   for clusters.

Dependencies:
-------------
- `pandas`
- `geopandas`
- `numpy`
- `seaborn`
- `scikit-learn`
"""


# %% Imports
from typing import Callable, Tuple, Union
import pandas as pd
import geopandas as gpd
import numpy as np
import seaborn as sns
from sklearn.metrics import silhouette_score


# -----------------------------------------------------------------------------
# Rare species filtering
# -----------------------------------------------------------------------------

def list_rare_species(df: pd.DataFrame, threshold: int) -> list:
    """
    Return scientific names of species with occurrences <= threshold.

    Args:
        df (pd.DataFrame): DataFrame containing a 'scientific_name' column.
        threshold (int): Max occurrences to consider a species rare.

    Returns:
        list (str): Rare species names.
    """
    counts = df['scientific_name'].value_counts()
    rare = counts[counts <= threshold].index.tolist()
    return rare


def remove_rare_species(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """
    Remove records of species with occurrences <= threshold.

    Args:
        df (pd.DataFrame): Input DataFrame with a 'scientific_name' column.
        threshold (int): Max occurrences to consider a species rare.

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    rare_species = list_rare_species(df, threshold)
    filtered = df[~df['scientific_name'].isin(rare_species)]
    return filtered


# -----------------------------------------------------------------------------
# Species counts per cell
# -----------------------------------------------------------------------------

def make_counts_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot to count species per grid cell.

    Args:
        df (pd.DataFrame): Contains 'grid_id' and 'scientific_name' columns.

    Returns:
        pd.DataFrame: Rows=grid_id, cols=species counts.
    """
    pivot = (
        df
        .pivot_table(
            index='grid_id',
            columns='scientific_name',
            aggfunc='size',
            fill_value=0
        )
        .reset_index()
    )
    # Flatten columns
    if isinstance(pivot.columns, pd.MultiIndex):
        pivot.columns = [col[1] if col[1] else col[0] for col in pivot.columns]
    return pivot


# -----------------------------------------------------------------------------
# Merge model results into GeoDataFrame
# -----------------------------------------------------------------------------

def merge_model_results(
    grid_gdf: 'gpd.GeoDataFrame',
    cell_ids: list[int],
    cluster_labels: list[int],
    model_name: str
) -> 'gpd.GeoDataFrame':
    """
    Merge cluster labels into spatial grid.

    Args:
        grid_gdf (GeoDataFrame): Contains 'grid_id'.
        cell_ids (list): Grid IDs matching labels order.
        cluster_labels (list): Labels per grid cell.
        model_name (str): Column name for labels.

    Returns:
        GeoDataFrame: With new model column.
    """
    data = pd.DataFrame({'grid_id': cell_ids, model_name: cluster_labels})
    merged = grid_gdf.merge(data, on='grid_id', how='left')
    return merged


# -----------------------------------------------------------------------------
# Cluster number selection
# -----------------------------------------------------------------------------

def select_best_k(
    x: np.ndarray,
    model_class: Callable,
    k_range: Union[range, list[int]],
    model_kwargs: dict = None,
    scoring: str = 'auto',
    random_state: int = 0
) -> Tuple[pd.DataFrame, int]:
    """
    Select optimal k for clustering models via BIC/AIC or silhouette.

    Args:
        X (np.ndarray): Feature matrix.
        model_class (Callable): Clustering model class, e.g.
        GaussianMixture or SpectralClustering.
        k_range (range or list): Range of k values to test.
        model_kwargs (dict): Additional args for the model.
        scoring (str): Metric to select best k
        ('auto', 'bic', 'aic', or 'silhouette').
        random_state (int): For reproducibility.

    Returns:
        results_df (pd.DataFrame): Scores for each k.
        best_k (int): optimizes the chosen metric.
    """
    if model_kwargs is None:
        model_kwargs = {}
    results = []

    for k in k_range:
        kwargs = model_kwargs.copy()

        if 'GaussianMixture' in model_class.__name__:
            kwargs['n_components'] = k
            kwargs['random_state'] = random_state
        else:
            kwargs['n_clusters'] = k
            if 'random_state' in model_class().get_params():
                kwargs['random_state'] = random_state

        model = model_class(**kwargs)

        if hasattr(model, 'bic') and scoring in ['auto', 'bic', 'aic']:
            model.fit(x)
            if scoring == 'auto':
                metric = 'bic'
            else:
                metric = scoring
            score = getattr(model, metric)(x)
            direction = 'min'
        else:
            # fallback: use silhouette score
            if hasattr(model, 'fit_predict'):
                labels = model.fit_predict(x)
            else:
                model.fit(x)
                labels = model.predict(x)
            if len(set(labels)) > 1:
                score = silhouette_score(x, labels)
            else:
                score = np.nan
            metric = 'silhouette'
            direction = 'max'

        results.append({'k': k, metric: score})

    df = pd.DataFrame(results)

    if direction == 'min':
        best_k = int(df.loc[df[metric].idxmin(), 'k'])
    else:
        best_k = int(df.loc[df[metric].idxmax(), 'k'])

    return df, best_k


# -----------------------------------------------------------------------------
# Map utilities
# -----------------------------------------------------------------------------

def categorise_opacity(score: float) -> float:
    """
    Categorise a weighted richness score (0-1) into one of four opacity levels:
        - Very low (< 0.01)  → 0.2
        - Low      (< 0.1)   → 0.4
        - Medium   (< 0.66)  → 0.8
        - High     (≥ 0.66)  → 0.98

    Args:
        score (float): Richness score between 0 and 1.
    Returns:
        float: Opacity level (0.2, 0.4, 0.8, or 0.98).
    """
    if score < 0.01:
        return 0.2
    if score < 0.1:
        return 0.4
    if score < 0.66:
        return 0.8
    return 0.98


def generate_cluster_colors(num_clusters: int) -> dict:
    """
    Generate a dictionary of unique colours for each cluster.

    Each cluster ID is formatted as a string with one decimal (e.g., '0.0').

    Args:
        num_clusters (int): Number of clusters.

    Returns:
        dict: {cluster_id: hex_colour}.
    """

    palette = sns.color_palette('Set2', num_clusters).as_hex()
    colors = {f"{i}.0": palette[i] for i in range(num_clusters)}
    colors['Without_data'] = '#4D4D4D'

    return colors
