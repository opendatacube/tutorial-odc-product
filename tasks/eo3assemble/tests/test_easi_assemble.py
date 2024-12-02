# pytest usage guided by:
# https://www.nerdwallet.com/blog/engineering/5-pytest-best-practices/
# https://realpython.com/pytest-python-testing/

import pytest

# Uncomment when required
# import datetime
# try:
#     # dateutil: >= 2.8.1
#     import dateutil.parser.ParserError as DateutilParserError
# except ImportError:
#     DateutilParserError = ValueError

from tasks.eo3assemble.easi_assemble import EasiPrepare, OUTPUT_NAME

def test_easiprepare_init_local_dir(dataset_dir, product_file):
    ep = EasiPrepare(str(dataset_dir), product_file)
    assert ep._dataset_scheme == 'file'
    assert ep._dataset_path == dataset_dir
    assert ep._dataset_bucket == None
    assert ep._dataset_key == None
    assert ep._output_path == dataset_dir / OUTPUT_NAME

def test_easiprepare_init_local_file(dataset_file, product_file):
    ep = EasiPrepare(str(dataset_file), product_file)
    assert ep._dataset_scheme == 'file'
    assert ep._dataset_path == dataset_file
    assert ep._dataset_bucket == None
    assert ep._dataset_key == None
    assert ep._output_path == dataset_file.parent / OUTPUT_NAME

def test_easiprepare_init_uri_dir(dataset_dir, product_file):
    file_scheme = f'file://{str(dataset_dir)}'
    ep = EasiPrepare(file_scheme, product_file)
    assert ep._dataset_scheme == 'file'
    assert ep._dataset_path == dataset_dir
    assert ep._dataset_bucket == None
    assert ep._dataset_key == None
    assert ep._output_path == dataset_dir / OUTPUT_NAME

def test_easiprepare_init_uri_file(dataset_file, product_file):
    file_scheme = f'file://{str(dataset_file)}'
    ep = EasiPrepare(file_scheme, product_file)
    assert ep._dataset_scheme == 'file'
    assert ep._dataset_path == dataset_file
    assert ep._dataset_bucket == None
    assert ep._dataset_key == None
    assert ep._output_path == dataset_file.parent / OUTPUT_NAME

def test_easiprepare_init_s3(s3_fake_bucket_key, product_file, writeable_file):
    ep = EasiPrepare(s3_fake_bucket_key, product_file, str(writeable_file))
    assert ep._dataset_scheme == 's3'
    assert ep._dataset_path == s3_fake_bucket_key
    assert ep._dataset_bucket == 'some-bucket'
    assert ep._dataset_key == 'some-key/another-key'
    assert ep._output_path == writeable_file

def test_easiprepare_init_s3_fail(s3_fake_bucket_key, product_file):
    with pytest.raises(RuntimeError):
        ep = EasiPrepare(s3_fake_bucket_key, product_file)

@pytest.mark.parametrize(
    "test_input,expected",
    [
        pytest.param(
            {
                "mtuples": [('elevation', 'DEM'), ('WBM', 'waterbody_mask'), ('FLM', 'filling_mask')],
                "band_ids": {'DEM': 'DEM.tif', 'WBM': 'WBM.tif', 'FLM': 'FLM.tif'},
                "supplementary": {},
            },
            {
                "measurement2path": {'elevation': 'DEM.tif', 'WBM': 'WBM.tif', 'FLM': 'FLM.tif'},
            },
            id="match_band_ids"
        ),
        pytest.param(
            {
                "mtuples": [('elevation', 'dem'), ('wbm', 'waterbody_mask'), ('flm', 'filling_mask')],
                "band_ids": {'DEM': 'DEM.tif', 'WBM': 'WBM.tif', 'FLM': 'FLM.tif'},
                "supplementary": {'elevation': 'DEM', 'wbm': 'WBM', 'flm': 'FLM'},
            },
            {
                "measurement2path": {'elevation': 'DEM.tif', 'wbm': 'WBM.tif', 'flm': 'FLM.tif'},
            },
            id="match_supplementary"
        ),
    ]
)
def test_easiprepare_match_measurement_names_to_band_ids(test_input, expected):
    # Adds path from band_ids to masurement2path if band_ids key exists in mtuples tuple.
    # supplementary dictionary allows mtuples tuple values to be treated equivalently to user defined values.
    match_measurement_names_to_band_ids = staticmethod(EasiPrepare._match_measurement_names_to_band_ids)
    measurement2path = match_measurement_names_to_band_ids(None, test_input['mtuples'], test_input['band_ids'], test_input['supplementary'])
    assert measurement2path == expected["measurement2path"]