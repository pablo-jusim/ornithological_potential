# Funciones cortas de uso variado

# %% Importaciones
import pandas as pd


# %% Eliminar registros de especies raras (menos de x ocurrencias)

def listar_spp_raras(df, ocurrencia):
    '''
    Toma un pandas dataframe y devuelve una lista de nombres
    cientificos de especies con menos de "ocurrencia" ocurrencias.

    Parameters:
    df (pd.DataFrame): DataFrame con una columna 'scientific_name'.
    ocurrencia (int): Umbral máximo de ocurrencias para considerar una especie
    como rara.
    Returns:
    list: A list of scientific names of rare species.
    '''
    
    # Contar cuántas veces aparece cada especie
    conteo = df['scientific_name'].value_counts()
    # Filtrar especies que aparecen menos o igual que el umbral
    spp_raras = conteo[conteo <= ocurrencia].index.tolist()
    return spp_raras


def eliminar_spp_raras(data, ocurrencia):
    '''
    Elimina del registro las especies con una ocurrencia menor
    a cierto umbral

    Parameters:
    data (csv): Archivo csv con los datos de registro de especies.
    ocurrencia (int): Umbral máximo de ocurrencias para considerar una especie
    como rara.
    Returns:
    pandas df: Data frame con las mismas columnas que el csv original.
    '''

    # Cargar el arhivo csv como df
    df = data
    # Listar especies raras
    spp_raras = listar_spp_raras(df, ocurrencia)
    # Eliminar especies raras
    df_filtrado = df[~df['scientific_name'].isin(spp_raras)]
    return df_filtrado

# %% Contar registros de especies y devolver en un data frame


def crear_df_conteos(df):
    '''
    Cuenta los registros de cada celda y arma un df con los registros
    de todas las especies del dataframe, una por columna.
    Parameters:
    df (pd.DataFrame): DataFrame con las columnas 'grid_cell' y
     'scientific_name'
    Returns:
    pd.DataFrame: DataFrame con la cantidad de registros por celda
    '''

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

    # Aplanar MultiIndex de columnas si existiera
    if isinstance(pivot.columns, pd.MultiIndex):
        # para cada tupla, toma el valor no vacío
        pivot.columns = [
            col[1] if col[1] != '' else col[0]
            for col in pivot.columns
        ]

    return pivot

# %% Incorporar modelado a grilla espacial


def grillar_res_mod(grilla, id_grid, clusters, nombre):
    '''
    Esta funcion hace un merge entre una grilla de datos espaciales
    y los resultados de un modelo.
    Parameters:
    grilla (geopadas): Geopandas con nombres de celdas y coordenadas
    id_grid (index): Indice conteniendo los id de las celdas de la grilla
    clusters(array): Arreglo conteniendo el nro de cluster al que pertenece
    cada celda.
    nombre (str): Nombre del modelo
    Returns:
    grilla_add: Geopandas con resultados del modelo incorporados a la grilla
    '''

    data = {
        'grid_id': id_grid,
        nombre: clusters
    }
    df_mod = pd.DataFrame(data)

    grilla_add = grilla.merge(df_mod, on='grid_id', how='left')
    return grilla_add


# %% Pruebas


if __name__ == "__main__":
    # Prueba de la función
    ruta = '../data/interim/data_ebird.csv'
    archivo = pd.read_csv(ruta)
    tabla = crear_df_conteos(archivo)
    print(tabla)

