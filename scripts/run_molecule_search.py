#!/usr/bin/env python
"""
Script for running molecule search
"""
import argparse
import json
import sys
from datetime import datetime as dt

from sm.engine import DB
from sm.engine import Dataset
from sm.engine import DatasetManager
from sm.engine import ESExporter
from sm.engine import QueuePublisher
from sm.engine.util import SMConfig, logger, sm_log_config, init_logger
from sm.engine.search_job import SearchJob


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SM process dataset at a remote spark location.')
    parser.add_argument('--ds-id', dest='ds_id', type=str, help='Dataset id')
    parser.add_argument('--ds-name', dest='ds_name', type=str, help='Dataset name')
    parser.add_argument('--input-path', type=str, help='Path to a dataset location')
    parser.add_argument('--ds-config', type=str)
    parser.add_argument('--ds-metadata', type=str)
    parser.add_argument('--no-clean', dest='no_clean', action='store_true', help="Don't clean dataset txt files after job is finished")
    parser.add_argument('--config', dest='sm_config_path', type=str, help='SM config path')
    args = parser.parse_args()

    init_logger()
    SMConfig.set_path(args.sm_config_path)

    ds_id = args.ds_id or dt.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")

    sm_config = SMConfig.get_conf()
    db = DB(sm_config['db'])
    ds_man = DatasetManager(db, ESExporter(), mode='local')
    metadata = json.load(open(args.ds_metadata)) if args.ds_metadata else {}
    ds_config = json.load(open(args.ds_config))
    ds = Dataset(ds_id, args.ds_name, args.input_path, metadata, ds_config)
    ds_man.add_ds(ds)

    job = SearchJob(ds_id, args.sm_config_path, args.no_clean)
    try:
        job.run()
    except:
        sys.exit(1)

    sys.exit()
