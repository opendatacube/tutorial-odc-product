from pathlib import Path
from tasks.common import get_logger
import logging
from tasks.prepare_io_lulc_annual_v02_metadata import prepare_dataset

logger = get_logger(Path(__file__).stem, level=logging.INFO)

## Check the data collection path - data/sample_dataset
# Use a glob or a file PATTERN. Customise depending on the expected dir/file names
collection_path = Path('data')

# Use the FOO measurement to generate an iterator over the unique tile ids used in the filenames
tiles = collection_path.glob('*.tif')

for tile in tiles:
    tile_id = tile.stem
    logger.info(f'Processing {tile_id}')

    prepare_dataset(
        tile_id=tile_id,
        dataset_path=str(collection_path),
        product_definition="products/impact_observatory/io_lulc_annual_v02.yaml",
    )

logger.info("Processing complete.")