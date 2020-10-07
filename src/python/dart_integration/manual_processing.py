
import os,sys,json,logging,multiprocessing

from main_executor import main_executor
from upstream import upstream_main

def main(config_path):
    log_format = '[%(asctime)s] {P%(process)d:%(module)s:%(lineno)d} %(levelname)s - %(message)s'
    try:
        logging.basicConfig(level=logging.getLevelName(os.environ.get('LOGLEVEL', 'INFO').upper()),
                            format=log_format)
        log_level = logging.getLevelName(os.environ.get('LOGLEVEL', 'INFO').upper())
    except ValueError as e:
        logging.error(
            "Unparseable level {}, will use default {}.".format(os.environ.get('LOGLEVEL', 'INFO').upper(),
                                                                logging.root.level))
        log_level = logging.root.leve
    with open(config_path) as fp:
        config = json.load(fp)
    runtime_tmp = config['hume.tmp_dir']
    corpus_dir = os.path.join(config['hume.tmp_dir'],'corpus')
    cdr_list_path = os.path.join(runtime_tmp, 'file.list')

    with open(cdr_list_path, 'w') as fp:
        for f in os.listdir(corpus_dir):
            if f.endswith(".json"):
                p = os.path.join(corpus_dir,f)
                fp.write("{}\n".format(p))
    main_executor(config_path, cdr_list_path)
    # upload
    upstream_main(config_path, False)

if __name__ == "__main__":
    config_path = "/extra/config.json"
    main(config_path)