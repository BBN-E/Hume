import json
import logging
import os
import shutil

from main_executor import main_executor
from upstream import upstream_main


def main(config_path):
    log_format = '[%(asctime)s] {P%(process)d:%(module)s:%(lineno)d} %(levelname)s - %(message)s'
    try:
        logging.basicConfig(level=logging.getLevelName(os.environ.get('LOGLEVEL', 'INFO').upper()),
                            format=log_format)
    except ValueError as e:
        logging.error(
            "Unparseable level {}, will use default {}.".format(os.environ.get('LOGLEVEL', 'INFO').upper(),
                                                                logging.root.level))
    with open(config_path) as fp:
        config = json.load(fp)
    corpus_dir = os.path.join(config["hume.manual.cdr_dir"])
    pipeline_dir = os.path.join(config['hume.tmp_dir'], 'manual_processing_pipeline')
    if config.get("hume.manual.keep_pipeline_data", False) is False:
        shutil.rmtree(pipeline_dir, ignore_errors=True)
    os.makedirs(pipeline_dir, exist_ok=True)
    main_executor(config_path, corpus_dir, pipeline_dir, config.get("hume.external_ontology_version", None),
                  config.get("hume.external_ontology_path", None))
    # upload
    upstream_main(config_path, pipeline_dir, False)


if __name__ == "__main__":
    config_path = "/extra/config.json"
    main(config_path)
