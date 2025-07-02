# Ornithological Potential
# Author: Pablo Jusim

# Short utility functions

# %% Imports
from typing import Callable, Tuple, Union
import pandas as pd
import geopandas as gpd
import numpy as np
import seaborn as sns
from sklearn.metrics import silhouette_score


# %% List rare species based on occurrence threshold

def list_rare_species(df: pd.DataFrame, threshold: int) -> list:
    """
    Return a list of scientific names for species with occurrences less than
    or equal to the threshold.

    Args:
        df (pd.DataFrame): DataFrame containing a 'scientific_name' column.
        threshold (int): Maximum number of occurrences for a species
        to be considered rare.

    Returns:
        list: List of scientific names of rare species.
    """
    counts = df['scientific_name'].value_counts()
    rare = counts[counts <= threshold].index.tolist()
    return rare


# %% Remove rare species from dataset

def remove_rare_species(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """
    Remove records of species with occurrences less than or equal
    to the threshold.

    Args:
        df (pd.DataFrame): Input DataFrame with a 'scientific_name' column.
        threshold (int): Maximum number of occurrences to classify a species
        as rare.

    Returns:
        pd.DataFrame: Filtered DataFrame with rare species removed.
    """
    rare_species = list_rare_species(df, threshold)
    filtered = df[~df['scientific_name'].isin(rare_species)]
    return filtered


# %% Create counts DataFrame for each grid cell and species

def make_counts_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count records per grid cell and species, returning a pivoted DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing 'grid_id'
        and 'scientific_name' columns.

    Returns:
        pd.DataFrame: Pivot table DataFrame with counts per cell per species.
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
    # Flatten MultiIndex columns if present
    if isinstance(pivot.columns, pd.MultiIndex):
        pivot.columns = [col[1] if col[1] else col[0] for col in pivot.columns]
    return pivot


# %% Merge model results into spatial grid

def merge_model_results(
    grid_gdf: 'gpd.GeoDataFrame',
    cell_ids: list,
    cluster_labels: list,
    model_name: str
) -> 'gpd.GeoDataFrame':
    """
    Merge model output (cluster labels) into a spatial grid GeoDataFrame.

    Args:
        grid_gdf (GeoDataFrame): GeoDataFrame of spatial grid with 'grid_id'.
        cell_ids (list): List of grid cell IDs corresponding 
        to each observation.
        cluster_labels (list): Cluster label for each grid cell.
        model_name (str): Name of the model/output column.

    Returns:
        GeoDataFrame: Merged GeoDataFrame with a new column for model labels.
    """
    data = {'grid_id': cell_ids, model_name: cluster_labels}
    df_mod = pd.DataFrame(data)
    merged = grid_gdf.merge(df_mod, on='grid_id', how='left')
    return merged


# -----------------------------------------------------------------------------
# Model selection functions
# -----------------------------------------------------------------------------

def select_best_k(
    x: np.ndarray,
    model_class: Callable,
    k_range: Union[range, list],
    model_kwargs: dict = None,
    scoring: str = 'auto',  # auto = BIC/AIC if available, else silhouette
    random_state: int = 0
) -> Tuple[pd.DataFrame, int]:
    """
    Generic selector for optimal number of clusters/components.
    Works for models like GaussianMixture (bic/aic)
    and SpectralClustering (silhouette).

    Args:
        X (np.ndarray): Feature matrix.
        model_class (Callable): Clustering model class, e.g.
        GaussianMixture or SpectralClustering.
        k_range (range or list): Range of k values to test.
        model_kwargs (dict): Additional args for the model.
        scoring (str): Metric to select best k
        ('auto', 'bic', 'aic', or 'silhouette').
        random_state (int): For reproducibility (if model supports it).

    Returns:
        results_df (pd.DataFrame): Scores for each k.
        best_k (int): k that optimizes the chosen metric.
    """
    if model_kwargs is None:
        model_kwargs = {}

    results = []

    for k in k_range:
        kwargs = model_kwargs.copy()

        # Set correct parameter name
        if 'GaussianMixture' in model_class.__name__:
            kwargs['n_components'] = k
            kwargs['random_state'] = random_state
        else:
            kwargs['n_clusters'] = k
            if 'random_state' in model_class().get_params():
                kwargs['random_state'] = random_state

        model = model_class(**kwargs)

        if hasattr(model, 'bic') and scoring in ['auto', 'bic', 'aic']:
            model.fit(X)
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
# Map related axiliary functions
# -----------------------------------------------------------------------------

def categorise_opacity(score: float) -> float:
    """
    Categorise a weighted richness score (0–1) into one of four opacity levels:
        - Very low (< 0.01)  → 0.2
        - Low      (< 0.1)   → 0.4
        - Medium   (< 0.66)  → 0.8
        - High     (≥ 0.66)  → 0.98
    """
    if score < 0.01:
        return 0.2
    elif score < 0.1:
        return 0.4
    elif score < 0.66:
        return 0.8
    else:
        return 0.98


def generate_cluster_colors(num_clusters: int) -> dict:
    """
    Generate a dictionary of unique colours for each cluster.

    Each cluster ID is formatted as a string with one decimal (e.g., '0.0').

    Args:
        num_clusters (int): Number of clusters to colour.

    Returns:
        dict: Dictionary in the form { cluster_id: hex_colour }.
    """

    # Generate a distinct colour palette
    palette = sns.color_palette('Set2', num_clusters).as_hex()

    # Build the dictionary with keys like '0.0', '1.0', etc.
    colors_dict = {f"{i}.0": palette[i] for i in range(num_clusters)}

    # Add a fixed colour for data without a cluster
    colors_dict['Without_data'] = '#4D4D4D'

    return colors_dict
