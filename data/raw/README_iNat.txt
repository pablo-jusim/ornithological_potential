Dataset obtenido de iNaturalist (https://www.inaturalist.org)
Exportado en 2025-05-26T14:29:44Z
Inluye 38 columnas con características 15651 instancias. Cada instancia refiere a una observación independiente documentada y verificada de uno o más ejemplares de una especie de ave (clase Aves; Linnaeus, 1758) realizada en la Isla Grande, dentro de la provincia de Tierra del Fuego AeIAS, Argentina.

Consulta utilizada para obtener los datos:
quality_grade=research&identifications=any&geoprivacy=open&taxon_geoprivacy=open&place_id=9120&taxon_id=3&verifiable=true&spam=false

Detalle de la consulta:
quality_grade=research: La especie fue identificada positivamente por, al menos, dos personas.
geoprivacy=open: La ubicación es pública (esto excluye observaciones cuyo autor decidió ocultar la ubicación)
taxon_geoprivacy=open: La ubicación del taxón (orden, familia, género, especie, etc.) es pública (esto excluye ciertos taxones en peligro de extinción dado que no se publica su ubicación).
place_id=9120: Tierra del Fuego, Argentina
taxon_id=3: Clase Aves
verifiable=true: La observación tiene documentación de respaldo (foto, video o audio)

Columnas:
id (int): Unique, sequential identifier for the observation

uuid (str): Identificador único universal para la observación. Ver https://datatracker.ietf.org/doc/html/rfc9562

observed_on_string (str): Fecha/hora registrada por el observador

observed_on (date): Fecha normalizada de observación

time_observed_at (datetime): Fecha normalizada de observación

user_id (int): Unique, sequential identifier for the observer

user_name (str): Name of the observer, generally used for attribution on the site. This is an optional field and may be a pseudonym

created_at (datetime): Fecha de creación de la observación

quality_grade (str): Grado de calidad de la observación. Para más detalles, ver https://help.inaturalist.org/support/solutions/articles/151000169936

captive_cultivated (bool): Si el organismo está cautivo. Para más detalle, ver https://help.inaturalist.org/support/solutions/articles/151000169932

place_guess (str): Descripción de la localidad registrada por el observador

latitude (float): Latitud  pública visible de la ubicación de la observación

longitude (float): Longitud pública visible de la ubicación de la observación

positional_accuracy (int): Precisión de las coordenadas

private_place_guess (str; empty): Ubicación de la observaciónescrita por el observador si oculta la ubcación.

private_latitude(float; empty): Latitud privada, selecciona si la observación es privada o está oscurecida

private_longitude float; empty): Longitud privada, selecciona si la observación es privada o está oscurecida

public_positional_accuracy (int): Incerteza posicional máxima en metros

geoprivacy (str): Si el obervador eligió ocultar las coordenadas. Ver https://help.inaturalist.org/support/solutions/articles/151000169938

taxon_geoprivacy (str): Se aplicó una geoprivacidad limitada debido al estado de conservación del taxa en la identificación actual.

coordinates_obscured (bool): Si las coordenadas se han ocultado, o no, por una condición de geoprivacidad o por tratarse de un taxón vulnerable

positioning_method (str): Cómo se determinaron las coordenadas

positioning_device (str): Dispositivo usado para determinar las coordenadas

place_town_name (str): Nombre de la ciudad que contiene las coordenadas de la observación, si se sabe

place_county_name (str): Nombre del área administrativa de segundo nivel que contiene las coordenadas de la observación (ej. departamento)

place_state_name (str): Nombre del área administrativa de segundo nivel que contiene las coordenadas de la observación (ej. provincia)

place_country_name (str): Nombre de país que contiene las coordenadas de la observación

place_admin1_name (str): Nombre del sitio administrativo un rango debajo del nivel de país

place_admin2_name (str): Nombre del sitio administrativo dos rangos debajo del nivel de país

species_guess (str): Texto plano para el nombre del taxón observado; puede haber sido fijado por el observador durante la observación, pero también puede ser reemplazado por nombres canónicos localizados cuando cambia el taxón

scientific_name (str): Nombre científico del taxón observado según iNaturalist

common_name (str): Nmbre común del taxón observado según iNaturalist

iconic_taxon_name (str): Categoría taxonómica de nivel superior para el taxón observado

taxon_id (int): Identificador único y secuencial del taxón observado

taxon_order_name (str): Nombre del orden taxonómico que contiene el taxón observado

taxon_family_name (str): Nombre de la familia taxonómica que contiene el taxón observado

taxon_genus_name (str): Nombre del género taxonómico que contiene el taxón observado

taxon_subspecies_name (str): Nombre de la subespecie taxonómica que contiene el taxón observado


Para más información sobre los encabezados de columnas, vea https://www.inaturalist.org/terminology


