import copy
import logging
import os
import shutil
import sys

logger = logging.getLogger(__name__)

project_root = os.path.realpath(os.path.join(__file__, os.path.pardir, os.path.pardir))
sys.path.append(project_root)

from regrounding_cache.utils import build_doc_id_to_doc_path, read_metadata, write_metadata


def main(current_run_metadata_path, current_run_serif_list_path, cache_dir_path, output_serif_list_path,
         current_run_bert_npz_list_path, output_npz_list_path):
    os.makedirs(cache_dir_path, exist_ok=True)
    cache_serifxml_list_path = os.path.join(cache_dir_path, 'serifxmls.list')
    # Step 1, copy all current run's serifxml into cache
    serifxml_dir = os.path.join(cache_dir_path, "serifxmls")
    os.makedirs(serifxml_dir, exist_ok=True)
    if os.path.exists(current_run_serif_list_path) is False:
        par_dir_serif_list = os.path.normpath(os.path.join(current_run_serif_list_path, os.path.pardir))
        os.makedirs(par_dir_serif_list, exist_ok=True)
        with open(current_run_serif_list_path, 'w') as wfp:
            pass
    total_file_cnt = 0
    contain_sgm_cnt = 0
    with open(current_run_serif_list_path) as fp:
        for i in fp:
            i = i.strip()
            doc_id = os.path.basename(i)
            total_file_cnt += 1
            if doc_id.endswith(".sgm.xml"):
                contain_sgm_cnt += 1
                doc_id = doc_id[:-len(".sgm.xml")]
                shutil.copy2(i, os.path.join(serifxml_dir, "{}.xml".format(doc_id)))
            else:
                shutil.copy2(i, serifxml_dir)

    suffix_contains_sgm = True if (total_file_cnt > 0 and contain_sgm_cnt / total_file_cnt > 0.7) else False

    current_doc_id_to_serif_path = build_doc_id_to_doc_path(current_run_serif_list_path,
                                                            ".sgm.xml" if suffix_contains_sgm is True else ".xml")

    # create_new_serif_list
    cached_doc_id_to_serif_path = dict()
    with open(cache_serifxml_list_path, 'w') as wfp:
        for file in os.listdir(serifxml_dir):
            full_path = os.path.join(serifxml_dir, file)
            doc_id = os.path.basename(full_path)
            doc_id = doc_id[:-len(".xml")]
            cached_doc_id_to_serif_path[doc_id] = full_path
            wfp.write("{}\n".format(full_path))

    # Maintain Metadata
    cache_doc_uuid_to_metadata_entries = dict()
    cache_metadata_path = os.path.join(cache_dir_path, 'metadata.txt')
    if os.path.exists(cache_metadata_path):
        _, cache_doc_uuid_to_metadata_entries = read_metadata(cache_metadata_path)
    current_serif_id_to_metadata_entry, current_doc_uuid_to_metadata_entries = read_metadata(current_run_metadata_path)
    consolidated_doc_uuid_to_metadata_entries = copy.deepcopy(cache_doc_uuid_to_metadata_entries)
    for doc_uuid, metadata_entries in current_doc_uuid_to_metadata_entries.items():
        consolidated_doc_uuid_to_metadata_entries[doc_uuid] = metadata_entries
    metadata_entries = list()
    for doc_uuid, entries in consolidated_doc_uuid_to_metadata_entries.items():
        metadata_entries.extend(entries)
    write_metadata(metadata_entries, cache_metadata_path)
    # All Serif Ids mentioned in current run
    all_serif_ids_in_current_run = current_serif_id_to_metadata_entry.keys()
    from_cache = 0
    from_current_run = 0
    missed = 0
    with open(output_serif_list_path, 'w') as wfp:
        for serif_id in all_serif_ids_in_current_run:
            if serif_id in current_doc_id_to_serif_path:
                from_current_run += 1
                wfp.write("{}\n".format(current_doc_id_to_serif_path[serif_id]))
            elif serif_id in cached_doc_id_to_serif_path:
                from_cache += 1
                wfp.write("{}\n".format(cached_doc_id_to_serif_path[serif_id]))
            else:
                missed += 1
    logger.info("[SerifXML]From current run: {}".format(from_current_run))
    logger.info("[SerifXML]From cache: {}".format(from_cache))
    logger.info("[SerifXML]Missed: {}".format(missed))
    if current_run_bert_npz_list_path != "NON_EXISTED_PATH":
        if os.path.exists(current_run_bert_npz_list_path) is False:
            par_dir_npz_list = os.path.normpath(os.path.join(current_run_bert_npz_list_path, os.path.pardir))
            os.makedirs(par_dir_npz_list, exist_ok=True)
            with open(current_run_bert_npz_list_path, 'w') as wfp:
                pass
        npzs_dir = os.path.join(cache_dir_path, "npzs")
        os.makedirs(npzs_dir, exist_ok=True)
        with open(current_run_bert_npz_list_path) as fp:
            for i in fp:
                i = i.strip()
                shutil.copy2(i, npzs_dir)
        current_doc_id_to_npz_path = build_doc_id_to_doc_path(current_run_bert_npz_list_path)
        cached_doc_id_to_npz_path = dict()
        cache_npzs_list_path = os.path.join(cache_dir_path, 'npzs.list')
        with open(cache_npzs_list_path, 'w') as wfp:
            for file in os.listdir(npzs_dir):
                full_path = os.path.join(npzs_dir, file)
                doc_id = os.path.basename(full_path)
                doc_id = doc_id[:-len(".npz")]
                cached_doc_id_to_npz_path[doc_id] = full_path
                wfp.write("{}\n".format(full_path))
        npz_from_cache = 0
        npz_from_current_run = 0
        npz_missed = 0
        with open(output_npz_list_path, 'w') as wfp:
            for serif_id in all_serif_ids_in_current_run:
                if serif_id in current_doc_id_to_npz_path:
                    npz_from_current_run += 1
                    wfp.write("{}\n".format(current_doc_id_to_npz_path[serif_id]))
                elif serif_id in cached_doc_id_to_npz_path:
                    npz_from_cache += 1
                    wfp.write("{}\n".format(cached_doc_id_to_npz_path[serif_id]))
                else:
                    npz_missed += 1
        logger.info("[NPZ]From current run: {}".format(npz_from_current_run))
        logger.info("[NPZ]From cache: {}".format(npz_from_cache))
        logger.info("[NPZ]Missed: {}".format(npz_missed))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--current_run_metadata_path", type=str, required=True)
    parser.add_argument("--current_run_serif_list_path", type=str, required=True)
    parser.add_argument("--cache_dir_path", type=str, required=True)
    parser.add_argument("--output_serif_list_path", type=str, required=True)
    parser.add_argument("--current_run_bert_npz_list_path", type=str, required=False, default="NON_EXISTED_PATH")
    parser.add_argument("--output_npz_list_path", type=str, required=False, default="NON_EXISTED_PATH")
    args = parser.parse_args()
    main(args.current_run_metadata_path, args.current_run_serif_list_path, args.cache_dir_path,
         args.output_serif_list_path, args.current_run_bert_npz_list_path, args.output_npz_list_path)
