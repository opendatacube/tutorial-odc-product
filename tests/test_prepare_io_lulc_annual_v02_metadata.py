import pytest
import yaml
from tasks.prepare_io_lulc_annual_v02_metadata import prepare_dataset

@pytest.fixture
def tile_id():
    return "15M-2017"

@pytest.fixture
def dataset_path():
    return "data"

@pytest.fixture
def product_definition():
    product_definition = "products/impact_observatory/io_lulc_annual_v02.yaml"
    return product_definition

def test_prepare_dataset(tile_id, dataset_path, product_definition):
    output_path = "data" # output path for the metadata file
    result = prepare_dataset(
        tile_id=tile_id,
        dataset_path=str(dataset_path),
        product_definition=product_definition,
        output_path=str(output_path)
    )
    assert result.exists()
    assert result.suffix == ".yaml"
    # load and compare two yaml file - the fixture will need to be generated and validated manually, so this is only regression testing.
    with open(result, 'r') as result_file:
        result_data = yaml.safe_load(result_file)

    with open("tests/fixture/fixture-odc-metadata.yaml", 'r') as expected_file:
        expected_data = yaml.safe_load(expected_file)

    assert result_data == expected_data

