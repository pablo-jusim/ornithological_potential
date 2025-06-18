# Potencial Ornitologico Fueguino
### **Autor:** Pablo Jusim

<img src="data/external/Carpintero.jpeg" alt="drawing" width="200"/>

## Contenidos
1. [Introducción](#introducción)
2. [Objetivos](#objetivos)  
3. [Origen de los datos](#origen-de-los-datos)  
4. [Línea de trabajo](#línea-de-trabajo)  
5. [Resultados](#resultados)  
6. [Conclusiones](#conclusiones)  
7. [Debilidades](#debilidades-del-proyecto)  
8. [Organización del proyecto](#organización-del-proyecto)  
9. [Instalación y uso](#instalación-y-uso)  
10. [Licencia](#licencia)
11. [Contacto](#contacto)


## Introducción
El turismo de observación de aves u ornitológico está en pleno creciemiento a nivel mundial. Esta clase de turismo trae un bajo impacto ambiental al tiempo que permite el ingreso de divisas. En la provincia de Tierra del Fuego, Argentina, la observación turística de aves está en un estado incipiente. Para formentar esta actividad, sería valorable contar con una clasificación territorial que permita saber a que sitios ir para observar la mayor cantidad de especies posibles, destacando especies raras o endémicas.

## **Objetivos**
### Objetivo general
Descubrir los mejores sitios de la provincia de Tierra del Fuego para llevar turistas que deseen realizar observación de aves.

### Objetivos particulares
- Clasificar cada celda de la provincia de Tierra del Fuego en un cluster según las especies de aves registradas
- Identificar los sitios con mayor potencial ornitológico dentro de cada cluster

<img src="data/external/Pingüino_rey.jpeg" alt="drawing" width="200"/>

## Origen de los datos
Se trabajó con registros de especies de aves realizados en las plataformas de **ciencia ciudadana** [iNaturalist](https://www.inaturalist.org) y [eBird](https://ebird.org/). Los datos son libres y fueron solicitados a ambas plataformas. Se solicitaron todos los datos disponibles de registros de aves en la provincia de Tierra del Fuego, Argentina.

## Línea de trabajo
Cada punto indicado corresponde a un notebook con idéntica numeración

1a. Limpieza y preparación de datos obtenidos de iNaturalist
1b. Limpieza y preparación de datos obtenidos de eBird
2. Confección de la base de datos a utilizarse en la clasificación de sitios (celdas)
3. Clusterización de las celdas en base a las especies registradas
4. Detección de las mejores celdas para observación en cada cluster en base a la riqueza específica y creación de mapas.

## Resultados
- Se dividió a la provincia de Tierra del Fuego en tres clusters según las especies de aves presentes
- Se obtuvo una grilla clusterizada de la provincia
- Se destacaron los mejores sitios para observación de aves en cada cluster
- Se creó un mapa mostrando la grilla clusterizada y la riqueza relativa de cada celda

<img src="reports/figures/Captura mapa interactivo.jpg" alt="drawing"/>

<p></p>
<p>Aquí se observa una captura de pantalla del mapa final. Para ver el mapa interactivo consulte la ruta "reports/figures/mapa_interactivo.html"</p>

## Conclusiones

A partir de los datos obtenidos de las plataformas iNaturalist y eBird se seleccionaron los **mejores sitios** para llevar turistas que deseen observar la mayor cantidad de aves que habitan en la provincia de Tierra del Fuego en la menor cantidad de salidas posible. Si un observador de aves desea visitar Tierra del Fuego debería priorizar recorrer:
- el área costera de Bahía Ushuaia, incluyendo el área de la reserva Bahía Encerrada;
- el Parque Nacional Tierra del Fuego
- las cercanías de la ciudad de Río Grande

Tanto los notebook de este proyecto como las funciones desarrolladas *ad-hoc* pueden ser utilizados para la clasificación de sitios en **cualquier lugar del mundo**, siempre y cuando se disponga de los datos correspondientes. Solo se requiere obtener los datos de las mismas fuentes (los cuales están disponibles tras el registro) y crear un mapa de contorno del área.

## Debilidades del proyecto
- Gran cantidad de celdas no cuentan con registros en las mencionadas plataformas. Si bien zonas como península Mitre no serían visitables por su aislamiento geográfico, otras zonas al norte del lago Khami en las ceranías de la frontera cuentan con rutas de acceso y podrían presentar una mayor riqueza de especies.
- Se decidió utilizar unicamente registros de ciencia ciudadana ya que la forma de obtenerlos es similar a los medios con los que cuentan los turistas (binoculares y cámara fotográfica). Sin embargo, esta metología excluye tanto a los registros realizados por la comunidad científica como los sitios poco visitados. Con registros más completos los clusters obtenidos podrían ser ligeramente diferentes, al igual que las celdas recomendadas.

<img src="data/external/Condor.jpeg" alt="drawing" width="400"/>

## Organización del proyecto

```
├── LICENSE            <- Licencia de código abierto
├── Makefile           <- Makefile con comandos útiles como `make data` o `make train`.
├── README.md          <- Archivo README principal con el resumen del proyecto.
├── data
│   ├── external       <- Datos e imágenes de fuentes externas (terceros).
│   ├── interim        <- Datos intermedios que han sido transformados.
│   ├── processed      <- Conjuntos de datos finales.
│   └── raw            <- Volcado de datos original para el modelado.
│
├── notebooks          <- Notebooks de Jupyter para procesar y modelar los datos
│   ├── 01a-conversion_inat.ipynb       <- Limpieza de datos iNaturalist.
│   ├── 01b-conversion_ebird.ipynb      <- Limpieza de datos eBird.
│   ├── 02-preparacion_df.ipynb         <- Creación de base de datos para modelado.
|   ├── 03-main.ipynb                   <- Clusterización de la grilla.
│   └── 04-postprocesamiento.ipynb      <- Evaluación de riqueza y creación de mapas.
│
├── pyproject.toml     <- Archivo de configuración del proyecto
│
├── references         <- Material de referencia.
│
├── reports            <- Análisis generados en formatos HTML, PDF, LaTeX, etc.
│   └── figures        <- Gráficos y figuras generadas para ser utilizadas en los informes,
│                          incluyendo mapas interactivos.
│
├── requirements.txt   <- Archivo de requerimientos para reproducir el entorno de análisis, por ejemplo:
│                         generado con `pip freeze > requirements.txt`.
│
├── setup.cfg          <- Archivo de configuración para flake8
|
└── src                <- Código fuente del proyecto. Contiene funciones auxiliares utilizadas en los notebooks.
    ├── __pycache__/    <- Archivos temporales generados automáticamente por Python.
    ├── utils.py        <- Funciones generales reutilizables.
    ├── grillado.py     <- Funciones para crear la grilla en base al mapa de contorno.
    └── asociar_griila.py  <- Funciones para gasociar observaciones a la celda correspondiente.
```

## Instalación y uso

1. Clonar el repositorio  

   ```bash
   git clone https://github.com/pablo-jusim/Potencial-ornitologico-fueguino.git
   cd Potencial-ornitologico-fueguino
   ```

2. Crear entorno e instalar dependencias  

    ```bash
    python3 -m venv venv
    source venv/bin/activate    # o venv\Scripts\activate en Windows
    pip install -r requirements.txt
    ```

3. Descargar los datos de eBird desde su servidor o desde [google drive](https://drive.google.com/file/d/1Dlc4CDrUaHSdlqO_qWHAMROhHPoJIOhG/view?usp=sharing).

4. Ejecutar los notebook en el orden indicado

## Licencia

Este proyecto se distribuye bajo la licencia MIT.  
Ver [LICENSE](LICENSE) para más detalles.

## Contacto
pablo.jusim@gmail.com



--------