import pytest
import numpy as np
from mock import patch, MagicMock
from numpy.testing import assert_array_equal

from sm.engine import DatasetReader, DB
from sm.engine.util import SMConfig
from sm.engine.work_dir import WorkDirManager
from sm.engine.tests.util import sm_config, ds_config, spark_context, create_test_db, drop_test_db


@pytest.fixture()
def create_drop_db(create_test_db, drop_test_db):
    pass


def test_dataset_reader_get_sample_area_mask_correctness(sm_config, spark_context, create_drop_db):
    SMConfig._config_dict = sm_config

    work_dir_man_mock = MagicMock(WorkDirManager)
    work_dir_man_mock.ds_coord_path = '/ds_path'
    work_dir_man_mock.txt_path = '/txt_path'

    with patch('sm.engine.tests.util.SparkContext.textFile') as m:
        m.return_value = spark_context.parallelize([
            '0,0,0\n',
            '2,1,1\n'])

        ds_reader = DatasetReader('ds_id', 'input_path', spark_context, work_dir_man_mock)
        ds_reader._determine_pixel_order()

        assert tuple(ds_reader.get_sample_area_mask()) == (True, False, False, True)


def test_dataset_reader_get_spectra_works(sm_config, spark_context, create_drop_db):
    SMConfig._config_dict = sm_config

    work_dir_man_mock = MagicMock(WorkDirManager)
    work_dir_man_mock.ds_coord_path = '/ds_path'
    work_dir_man_mock.txt_path = '/txt_path'

    with patch('sm.engine.tests.util.SparkContext.textFile') as m:
        m.side_effect = [spark_context.parallelize(['0|100.0 200.0|1000.0 0\n', '2|200.0 300.0|10.0 20.0\n'])]

        ds_reader = DatasetReader('ds_id', 'input_path', spark_context, work_dir_man_mock)
        spectra_list = ds_reader.get_spectra().collect()

        assert map(lambda t: t[0], spectra_list) == [0, 2]
        first_spectra = spectra_list[0]
        assert_array_equal(first_spectra[1], np.array([100.0, 200.0]))
        assert_array_equal(first_spectra[2], np.array([1000.0, 0]))
        second_spectra = spectra_list[1]
        assert_array_equal(second_spectra[1], np.array([200.0, 300.0]))
        assert_array_equal(second_spectra[2], np.array([10.0, 20.0]))