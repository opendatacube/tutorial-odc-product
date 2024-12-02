#!python3
# Prepare eo3 metadata for one SAMPLE DATASET.
#
## Main steps
# 1. Populate EasiPrepare class from source metadata
# 2. Call p.write_eo3() to validate and write the dataset YAML document

import re
import uuid
import warnings
from pathlib import Path
import logging
from datetime import datetime

from eodatasets3.images import ValidDataMethod
from tasks.eo3assemble.easi_assemble import EasiPrepare
from tasks.common import get_logger

logger = get_logger(Path(__file__).stem, level=logging.INFO)

# Static namespace (seed) to generate uuids for datacube indexing
# Get a new seed value for a new driver from uuid4():
# Python terminal
# >>> import uuid
# >>> uuid.uuid4()
UUID_NAMESPACE = uuid.UUID('e088ac10-9b1a-400d-ac53-b1aaf13f5d83')

def prepare_dataset(
    tile_id: str,
    dataset_path: str,
    product_definition: Path,
    output_path: str = None,
) -> Path:
    """
    Prepare an eo3 metadata file for SAMPLE data product.
    @param tile_id: Unique tile ID for a single dataset to prepare.
    @param dataset_path: Directory of the datasets (top level Product collection).
    @param product_definition: Path to the product definition yaml file.
    @param output_path: Path to write the output metadata file.

    :return: Path to odc dataset yaml file
    """

    ## Initialise and validate inputs
    # Creates variables (see EasiPrepare for others):
    # - p.dataset_path
    # - p.product_name
    # The output_path and tile_id are use to create a dataset unique filename for the output metadata file
    # Variable p is a dictionary of metadata and measurements to be written to the output metadata file.
    # The code will populate p with the metadata and measurements and then call p.write_eo3() to write the output metadata file.
    if not output_path:
        output_path = dataset_path
    p = EasiPrepare(dataset_path, product_definition, f'{output_path}/{tile_id}-odc-metadata.yaml')

    ## File format of data
    # e.g. cloud-optimised GeoTiff (= GeoTiff)
    file_format = 'GeoTIFF'

    ## Ignore warnings, OPTIONAL
    # Ignore unknown property warnings (generated in eodatasets3.properties.Eo3Dict().normalise_and_set())
    # Eodatasets3 validates properties against a hardcoded list, which includes DEA stuff so no harm if we add our own
    custom_prefix = 'io'   # usually related to the product name or type - io = impact observatory in this case
    warnings.filterwarnings('ignore', message=f'.*Unknown stac property.+{custom_prefix}:.+')

    ## IDs and Labels should be dataset and Product unique
    unique_name = f'{tile_id}'  # Unique dataset name, probably parsed from p.dataset_path or a filename
    unique_name_replace = re.sub('\.', '_', unique_name) # Can not have '.' in label
    p.label = f"{unique_name_replace}-{p.product_name}"
    p.dataset_id = uuid.uuid5(UUID_NAMESPACE, p.label)  # Unique dataset UUID built from the unique Product ID
    p.product_uri = f"https://products.easi-eo.solutions/{p.product_name}"  # product_name is added by EasiPrepare().init()

    ## Satellite, Instrument and Processing level
    p.platform = 'ImpactObservatory'  # High-level name for the source data (satellite platform or project name). Comma-separated for multiple platforms.
    # p.instrument = 'SAMPLETYPE'  #  Instrument name, optional
    p.producer = 'www.impactobservatory.com'  # Organisation that produces the data. URI domain format containing a '.'
    # p.product_family = 'FAMILY_STUFF'  # ODC/EASI identifier for this "family" of products, optional
    p.properties['odc:file_format'] = file_format  # Helpful but not critical

    ## Scene capture and Processing
    pattern = r"(?P<supercell_id>\d+[A-Z]+)-(?P<year>\d{4})"
    match = re.match(pattern, tile_id)
    if match:
        p.properties[f'{custom_prefix}:supercell_id'] = match.group('supercell_id')
        p.properties[f'{custom_prefix}:year'] = match.group('year')
        p.datetime = f"{match.group('year')}-01-01T00:00:00"  # Searchable datetime of the dataset, datetime object - appears to be only in the file name tile ID for this dataset
        p.processed = f"{match.group('year')}-01-01T00:00:00"  # Processing datetime, datetime object
    else:
        raise ValueError(f"Tile ID {tile_id} does not match the pattern {pattern}")
    p.dataset_version = 'v1.3'  # The version of the source dataset, also made up but you will want it! - obtained from https://docs.impactobservatory.com/tutorials/aws-open-data-exchange/aws-open-data-exchange.html

    ## Geometry
    # Geometry adds a "valid data" polygon for the scene, which helps bounding box searching in ODC
    # Either provide a "valid data" polygon or calculate it from all bands in the dataset
    # Some techniques are more accurate than others, but all are valid. You may need to use coarser methods if the data
    # is particularly noisy or sparse.
    # ValidDataMethod.thorough = Vectorize the full valid pixel mask as-is
    # ValidDataMethod.filled = Fill holes in the valid pixel mask before vectorizing
    # ValidDataMethod.convex_hull = Take convex-hull of valid pixel mask before vectorizing
    # ValidDataMethod.bounds = Use the image file bounds, ignoring actual pixel values
    # p.geometry = Provide a "valid data" polygon rather than read from the file, shapely.geometry.base.BaseGeometry()
    # p.crs = Provide a CRS string if measurements GridSpec.crs is None, "epsg:*" or WKT
    p.valid_data_method = ValidDataMethod.bounds

    ## Product-specific properties, OPTIONAL
    # For examples see eodatasets3.properties.Eo3Dict().KNOWN_PROPERTIES
    # p.properties[f'{custom_prefix}:algorithm_version'] = ''
    # p.properties[f'{custom_prefix}:doi'] = ''
    # p.properties[f'{custom_prefix}:short_name'] = ''
    # p.properties[f'{custom_prefix}:processing_system'] = 'SomeAwesomeProcessor' # as an example

    ## Add measurement paths
    # This simple loop will go through all the measurements and determine their grids, the valid data polygon, etc
    # and add them to the dataset.
    # For LULC there is only one measurement, land_cover_class
    p.note_measurement(
        "land_cover_class",
        f"{dataset_path}/{tile_id}.tif",
        relative_to_metadata = True
    )

    ## Complete validate and return
    # validation is against the eo3 specification and your product/dataset definitions
    try:
        dataset_uuid, output_path = p.write_eo3()
    except Exception as e:
        raise e
    logger.info(f'Wrote dataset {dataset_uuid} to {output_path}')
    return output_path
