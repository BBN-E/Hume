import os


def read_metadata(input_metadata_path):
    doc_uuid_to_entries = dict()
    serif_id_to_entry = dict()
    with open(input_metadata_path) as fp:
        for i in fp:
            i = i.strip()
            serif_doc_id, cdr_path_in_file_system, creation_date, confidence, doc_type, sgm_path, cdr_uuid, offset, author, source_uri = i.split(
                "\t")
            en = {
                "serif_doc_id": serif_doc_id,
                "cdr_path_in_file_system": cdr_path_in_file_system,
                "creation_date": creation_date,
                "confidence": confidence,
                "doc_type": doc_type,
                "sgm_path": sgm_path,
                "cdr_uuid": cdr_uuid,
                "offset": offset,
                "author": author,
                "source_uri": source_uri,
            }
            doc_uuid_to_entries.setdefault(cdr_uuid, list()).append(en)
            serif_id_to_entry[serif_doc_id] = en
    return serif_id_to_entry, doc_uuid_to_entries


def write_metadata(metadata_entries, output_path):
    with open(output_path,'w') as wfp:
        for metadata_entry in metadata_entries:
            wfp.write("{}\n".format("\t".join((
                metadata_entry['serif_doc_id'], metadata_entry['cdr_path_in_file_system'],
                metadata_entry['creation_date'], metadata_entry['confidence'],
                metadata_entry['doc_type'], metadata_entry['sgm_path'],
                metadata_entry['cdr_uuid'], metadata_entry['offset'],
                metadata_entry['author'], metadata_entry['source_uri']))))


def build_doc_id_to_doc_path(file_list_path, suffix=".xml"):
    doc_id_to_doc_path = dict()
    with open(file_list_path) as fp:
        for i in fp:
            i = i.strip()
            doc_id = os.path.basename(i)
            doc_id = doc_id[:-len(suffix)]
            doc_id_to_doc_path[doc_id] = i
    return doc_id_to_doc_path
