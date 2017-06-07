import json
from collections import OrderedDict
import numpy as np
import logging
import requests

from sm.engine.db import DB
from sm.engine.util import SMConfig
from sm.engine.png_generator import PngGenerator, ImageStoreServiceWrapper

logger = logging.getLogger('sm-engine')
METRICS_INS = 'INSERT INTO iso_image_metrics VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'


class SearchResults(object):
    """ Container for molecule search results

    Args
    ----------
    sf_db_id : int
        Formula database id
    job_id : int
        Search job id
    metric_names: list
        Metric names
    ds: engine.dataset.Dataset
    db: engine.db.DB
    """
    def __init__(self, sf_db_id, job_id, metric_names, ds, db):
        self.sf_db_id = sf_db_id
        self.job_id = job_id
        self.metric_names = metric_names
        self.ds = ds
        self.db = db
        self.sm_config = SMConfig.get_conf()

    def _metrics_table_row_gen(self, job_id, db_id, metr_df, ion_img_ids):
        for ind, r in metr_df.reset_index().iterrows():
            m = OrderedDict((name, r[name]) for name in self.metric_names)
            metr_json = json.dumps(m)
            ids = ion_img_ids[(r.sf_id, r.adduct)]
            yield (job_id, db_id, r.sf_id, r.adduct,
                   float(r.msm), float(r.fdr), metr_json,
                   ids['iso_image_ids'], None)

    def store_ion_metrics(self, ion_metrics_df, ion_img_ids):
        """ Store formula image metrics in the database """
        logger.info('Storing iso image metrics')

        rows = list(self._metrics_table_row_gen(self.job_id, self.sf_db_id,
                                                ion_metrics_df, ion_img_ids))
        self.db.insert(METRICS_INS, rows)

    def _get_post_images(self):
        png_generator = PngGenerator(self.ds.reader.coord_pairs, greyscale=True)
        img_store = ImageStoreServiceWrapper(self.sm_config['services']['iso_images'])

        def _post_images(imgs):
            imgs += [None] * (4 - len(imgs))

            iso_image_ids = [None] * 4
            for k, img in enumerate(imgs):
                if img is not None:
                    fp = png_generator.generate_png(img.toarray())
                    iso_image_ids[k] = img_store.post_image(fp)
            return {
                'iso_image_ids': iso_image_ids
            }

        return _post_images

    def post_images_to_image_store(self, ion_iso_images):
        logger.info('Posting iso images to {}'.format(self.sm_config['services']['iso_images']))
        post_images = self._get_post_images()
        return dict(ion_iso_images.mapValues(post_images).collect())

    def store(self, ion_metrics_df, ion_iso_images):
        logger.info('Storing search results to the DB')
        ion_img_ids = self.post_images_to_image_store(ion_iso_images)
        self.store_ion_metrics(ion_metrics_df, ion_img_ids)
