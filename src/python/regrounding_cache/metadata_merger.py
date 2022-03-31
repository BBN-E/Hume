import os, sys, logging

logger = logging.getLogger(__name__)

project_root = os.path.realpath(os.path.join(__file__, os.path.pardir, os.path.pardir))
sys.path.append(project_root)

from regrounding_cache.utils import read_metadata, write_metadata

def merge_metadata(output_metadata_path, input_metadata_paths):
    merged_doc_id_to_en = dict()
    for input_metadata_path in input_metadata_paths:
        serif_id_to_entry, doc_uuid_to_entries = read_metadata(input_metadata_path)
        merged_doc_id_to_en.update(serif_id_to_entry)
    write_metadata(merged_doc_id_to_en.values(), output_metadata_path)

if __name__ == "__main__":
    input_metadata_paths = [
        "/home/hqiu/tmp/metadata_remote.txt",
        "/home/hqiu/tmp/metadata_local.txt"
    ]
    output_metadata_path = "/home/hqiu/tmp/metadata.txt"
    merge_metadata(output_metadata_path, input_metadata_paths)