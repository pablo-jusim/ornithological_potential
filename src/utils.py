# Short utility functions

# %% Imports
import pandas as pd
import geopandas as gpd


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
        df (pd.DataFrame): DataFrame containing 'grid_id' and 'scientific_name' columns.

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


# %% Tests

if __name__ == '__main__':
    # Test make_counts_dataframe
    SAMPLE_PATH = '../data/interim/data_ebird.csv'
    df_sample = pd.read_csv(SAMPLE_PATH)
    result = make_counts_dataframe(df_sample)
    print(result.head())

