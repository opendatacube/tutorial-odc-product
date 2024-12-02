# pytest fixtures

import pytest
import requests

# Not used but could be handy
@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    def stunted_get():
        raise RuntimeError("Network access not allowed during testing!")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: stunted_get())

SAMPLE_PRODUCT = '''
name: test_product
description: This is a test product
metadata_type: eo3
metadata:
    product:
        name: test_product
storage:
  crs: EPSG:4326
measurements:
-   dtype: float32
    name: test_data
    nodata: 0
    units: metre
'''

@pytest.fixture()
def product_file(tmp_path):
    p = tmp_path / 'test_product.yaml'
    with p.open('w') as f:
        f.write(SAMPLE_PRODUCT)
    return p

@pytest.fixture
def dataset_dir(tmp_path):
    p = tmp_path / 'datadir'
    p.mkdir()
    return p

@pytest.fixture
def dataset_file(tmp_path):
    p = tmp_path / 'data.tif'
    with p.open('w') as f:
        f.write('sample tif data file')
    return p

@pytest.fixture
def writeable_file(tmp_path):
    p = tmp_path / 'writeable.txt'
    with p.open('w') as f:
        f.write('\n')
    return p

@pytest.fixture
def s3_fake_bucket_key():
    return 's3://some-bucket/some-key/another-key'
