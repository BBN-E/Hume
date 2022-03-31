import logging
import os
import sys

logger = logging.getLogger(__name__)

project_root = os.path.realpath(os.path.join(__file__, os.path.pardir, os.path.pardir))
sys.path.append(project_root)

from regrounding_cache.utils import build_doc_id_to_doc_path


def shrink_sgm_list(cache_dir_path, input_sgm_list_path, output_sgm_list_path):
    os.makedirs(cache_dir_path, exist_ok=True)
    cache_serifxml_list_path = os.path.join(cache_dir_path, 'serifxmls.list')
    serifxml_dir = os.path.join(cache_dir_path, "serifxmls")
    os.makedirs(serifxml_dir, exist_ok=True)
    cached_doc_id_to_serif_path = dict()
    with open(cache_serifxml_list_path, 'w') as wfp:
        for path in os.listdir(serifxml_dir):
            full_path = os.path.join(serifxml_dir, path)
            doc_id = os.path.basename(full_path)
            doc_id = doc_id[:-len(".xml")]
            cached_doc_id_to_serif_path[doc_id] = full_path
            wfp.write("{}\n".format(full_path))

    input_doc_id_to_sgm_path = build_doc_id_to_doc_path(input_sgm_list_path)
    total = 0
    hit = 0
    with open(output_sgm_list_path, 'w') as wfp:
        for doc_id, sgm_path in input_doc_id_to_sgm_path.items():
            total += 1
            if doc_id not in cached_doc_id_to_serif_path.keys():
                wfp.write("{}\n".format(sgm_path))
                logger.info("Will process {} through full extraction+grounding stages.".format(doc_id))
            else:
                logger.info("Will process {} through grounding stages only.".format(doc_id))
                hit += 1
    logger.info(
        "We'll process {} through extraction+grounding stages. We'll process {} through grounding stages only.".format(
            total - hit, hit))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--cache_dir_path", type=str, required=True)
    parser.add_argument("--input_sgm_list_path", type=str, required=True)
    parser.add_argument("--output_sgm_list_path", type=str, required=True)
    args = parser.parse_args()
    shrink_sgm_list(args.cache_dir_path, args.input_sgm_list_path, args.output_sgm_list_path)
