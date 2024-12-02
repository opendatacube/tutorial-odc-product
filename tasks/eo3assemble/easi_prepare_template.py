#!python3

## THIS IS A TEMPLATE ##
## Copy and Adapt for a source/product as necessary ##

# Prepare eo3 metadata for one DATASET.
# A directory of files represents one DATASET of MEASUREMENTS (files).
#
## Main steps
# 1. Parse source metadata
# 2. Populate EasiPrepare class from source metadata
# 3. Call p.write_eo3() to validate and write the dataset YAML document


import re
import uuid
import warnings
from pathlib import Path
import click
import logging

from eodatasets3.images import ValidDataMethod
from tasks.eo3assemble.easi_assemble import EasiPrepare
from tasks.common import get_logger

logger = get_logger(Path(__file__).stem, level=logging.INFO)


# Static namespace (seed) to generate uuids for datacube indexing
# Get a new seed value for a new driver from uuid4()
UUID_NAMESPACE = None  # FILL. Get from the product family or generate a new one with uuid.UUID(seed)

## Expected file patterns
# Can be used to select data or metadata files, or parse metadata from file names
# (example filename to be parsed)
PATTERN = re.compile('FILL')


## Functions to parse metadata
# Build a metadata dictionary that has keys for relevant items to be used below
def parse_metadata():
    """Parse useful variables into a dict"""
    return {}

def main(
        dataset_path: str,
    product_yaml: Path,
    output_path: str = None,
)
## Metadata
# a. Get or create metadata file from dataset_path
# b. Parse metadata to extract useful variables into a dict
## Assemble and output
# c. Use the dict values to populate the EasiPrepare object
#    Items labelled as 'FILL' are required
#    Items labelled as 'OPTIONAL' are optional but are often helpful. Populate them if possible
# d. Add the metadata file as an accessory file
def prepare_dataset(
    dataset_tile: str,
    product_yaml: Path,
    output_path: str = None,
) -> Path:
    """
    (template)
    Prepare an eo3 metadata file for [SOMETHING].

    Input dataset_path should be a [DIRECTORY, FILE or S3 URI].

    :return: Path to odc dataset yaml file
    """

    ## Initialise and validate inputs
    # Creates variables (see EasiPrepare for others):
    # - p.dataset_path
    # - p.product_name
    p = EasiPrepare(dataset_path, product_yaml, output_path)

    ## File format of preprocessed data
    # e.g. cloud-optimised GeoTiff (= GeoTiff)
    file_format = 'GeoTIFF'
    extension = 'tif'

    ## Check the p.dataset_path
    # Use a glob or a file PATTERN. Customise depending on the expected dir/file names and p.dataset_path
    # files = list(p.dataset_path.glob(f'*.{extension}'))
    dataset_pattern = PATTERN.search(p.dataset_path)   # Or files
    if not dataset_pattern:
        return False, f'Product ID does not match expected form: {p.dataset_path}'

    ## Files and Metadata
    # Recommendations:
    # - Use globs and regexs to find the expected data and accessory files
    # - Build a metadata dictionary that has keys for relevant items to be used below
    src_metadata_file = Path('FILL')
    thumbnail_file = Path('OPTIONAL')
    meta = parse_metadata(src_metadata_file)

    ## Ignore warnings, OPTIONAL
    # Ignore unknown property warnings (generated in eodatasets3.properties.Eo3Dict().normalise_and_set())
    # Eodatasets3 validates properties against a hardcoded list, which includes DEA stuff so no harm if we add our own
    custom_prefix = 'OPTIONAL'   # usually related to the product name or type
    warnings.filterwarnings('ignore', message=f'.*Unknown stac property.+{custom_prefix}:.+')

    ## IDs and Labels
    unique_name = 'FILL'  # Unique dataset name, probably parsed from p.dataset_path or a filename
    p.dataset_id = uuid.uuid5(UUID_NAMESPACE, unique_name)  # Unique dataset UUID
    unique_name_replace = re.sub('\.', '_', unique_name)
    p.label = f"{unique_name_replace}-{p.product_name}"  # Can not have '.' in label
    p.product_uri = f"https://products.easi-eo.solutions/{p.product_name}"  # product_name is added by EasiPrepare().init()

    ## Satellite, Instrument and Processing level
    p.platform = 'FILL'  # High-level name for the source data (satellite platform or project name). Comma-separated for multiple platforms.
    p.instrument = 'OPTIONAL'  #  Instrument name, optional
    p.producer = 'FILL'  # Organisation that produces the data. URI domain format containing a '.'
    p.product_family = 'OPTIONAL'  # ODC/EASI identifier for this "family" of products, optional
    p.properties['odc:file_format'] = file_format  # Helpful but not critical

    ## Scene capture and Processing
    p.datetime = 'FILL'  # Searchable datetime of the dataset, datetime object
    p.datetime_range = ('OPTIONAL', 'OPTIONAL')  # Searchable start and end datetimes of the dataset, datetime objects
    p.processed = 'FILL'   # When the source dataset was created by the producer, datetime object
    p.dataset_version = 'FILL'  # The version of the source dataset

    ## Geometry
    # Geometry adds a "valid data" polygon for the scene, which helps bounding box searching in ODC
    # Either provide a "valid data" polygon or calculate it from all bands in the dataset
    # ValidDataMethod.thorough = Vectorize the full valid pixel mask as-is
    # ValidDataMethod.filled = Fill holes in the valid pixel mask before vectorizing
    # ValidDataMethod.convex_hull = Take convex-hull of valid pixel mask before vectorizing
    # ValidDataMethod.bounds = Use the image file bounds, ignoring actual pixel values
    # p.geometry = Provide a "valid data" polygon rather than read from the file, shapely.geometry.base.BaseGeometry()
    # p.crs = Provide a CRS string if measurements GridSpec.crs is None, "epsg:*" or WKT
    if HAS_VALIDDATAMETHOD:
        p.valid_data_method = ValidDataMethod.filled

    ## Scene metrics, as available
    p.region_code = 'FILL'  # The "region" of acquisition, if applicable
    p.properties["eo:gsd"] = 'FILL'  # Nominal ground sample distance or spatial resolution
    # p.properties["eo:cloud_cover"] = 'OPTIONAL'
    # p.properties["eo:sun_azimuth"] = 'OPTIONAL'
    # p.properties["eo:sun_zenith"] = 'OPTIONAL'

    ## Product-specific properties, OPTIONAL
    # For examples see eodatasets3.properties.Eo3Dict().KNOWN_PROPERTIES
    # p.properties[f'{custom_prefix}:algorithm_version'] = ''
    # p.properties[f'{custom_prefix}:doi'] = ''
    # p.properties[f'{custom_prefix}:short_name'] = ''
    # p.properties[f'{custom_prefix}:processing_system'] = ''

    ## Add measurement paths
    # The regex selects a unique measurement or alias string from the data files (EDIT as necessary)
    measurement_map = p.map_measurements_to_paths(
        f'([\w_]+)\.{extension}'
    )
    for measurement_name, file_location in measurement_map.items():
        logger.debug(f'Measurement map: {measurement_name} > {file_location}')
        p.note_measurement(
            measurement_name,
            file_location,
            relative_to_metadata = True
        )

    ## Add references to accessory files
    # The actual accessory file(s) should also be saved with the data files
    p.note_accessory_file('metadata:FILL', src_metadata_file)

    # Thumbnails
    #
    # Explorer
    # https://github.com/opendatacube/datacube-explorer/blob/develop/cubedash/_filters.py#L128
    # get_dataset_file_offsets = {item name : path value}
    # select from only "thumbnail:nbart" or "thumbnail"
    # - not consistent with eo3??
    #
    # Thumbnail should be a public URL to be used by Explorer
    # If its sitting with the data in S3 then I think Explorer will convert it to an s3 HTTPS URL, which may or may not be public
    # If its a full HTTPS URL then it will be used directly.

    ## Create thumbnail (more info pending)
    # p.write_thumbnail(red="swir1", green="swir2", blue="red")

    if thumbnail_file:
        # p.note_accessory_file('thumbnail', thumbnail_file)  # Local file
        p.note_accessory_file('thumbnail', thumbnail_file, relative_to_metadata=False)  # Full URL

    ## Complete and return
    # write_eo3() = grids, validate, format and write
    try:
        dataset_uuid, output_path = p.write_eo3()
    except Exception as e:
        raise e
    logger.info(f'Wrote dataset {dataset_uuid} to {output_path}')
    return output_path


@click.command()
@click.argument(
    'dataset_path',
    type=str,
)
@click.argument(
    'product_yaml',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.option(
    '-o', '--output-path',
    type=str,
    default=None,
    help='Local path to write the metadata file. Default is alongside each dataset',

)
def cli(dataset_path, product_yaml, output_path):
    """
    Write an eo3 metadata file for a 'prepared' dataset.

    Input dataset_path can be a filesystem path or S3 URI.
    If dataset_path is a directory it should contain the data files.
    """
    main(dataset_path, product_yaml, output_path)


def prepare(*args, **kwargs):
    """Deprecated"""
    return main(*args, **kwargs)

def prepare_and_write(*args, **kwargs):
    """Deprecated"""
    return main(*args, **kwargs)

if __name__ == "__main__":
    cli()
