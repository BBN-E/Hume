import os
import logging


logger = logging.getLogger(__name__)

def read_metadata(input_metadata_file):
    doc_id_to_metadata_line = dict()
    doc_id_to_bucket_id = dict()
    with open(input_metadata_file, 'r') as o:
        for line in o:
            line = line.strip()
            pieces = line.split("\t")
            docid = pieces[0]
            doc_id_to_metadata_line[docid] = line
            doc_id_to_bucket_id[docid] = pieces[6] # This is UUID
    return doc_id_to_metadata_line,doc_id_to_bucket_id

def read_serif_list(input_serif_list,suffix=".xml"):
    doc_id_to_path = dict()
    with open(input_serif_list,'r') as fp:
        for i in fp:
            i = i.strip()
            docid = os.path.basename(i)[:-len(suffix)]
            doc_id_to_path[docid] = i
    return doc_id_to_path

def main(input_serif_list,input_metadata_file,output_dir):
    doc_id_to_metadata_line, doc_id_to_bucket_id = read_metadata(input_metadata_file)
    doc_id_to_path = read_serif_list(input_serif_list)
    bucket_id_to_doc_ids = dict()
    for doc_id,bucket_id in doc_id_to_bucket_id.items():
        if doc_id in doc_id_to_path:
            bucket_id_to_doc_ids.setdefault(bucket_id,set()).add(doc_id)
        else:
            logger.critical("Missing {} in the serif list".format(doc_id))

    for bucket_id,doc_ids in bucket_id_to_doc_ids.items():
        bucket_dir = os.path.join(output_dir,bucket_id)
        os.makedirs(bucket_dir,exist_ok=True)
        with open(os.path.join(bucket_dir,'metadata.txt'),'w') as metadatafp:
            with open(os.path.join(bucket_dir,'serifxml.list'),'w') as seriflistfp:
                for doc_id in doc_ids:
                    seriflistfp.write("{}\n".format(doc_id_to_path[doc_id]))
                    metadatafp.write("{}\n".format(doc_id_to_metadata_line[doc_id]))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_serif_list', required=True)
    parser.add_argument('--input_metadata_file', required=True)
    parser.add_argument('--output_dir', required=True)
    args = parser.parse_args()
    main(args.input_serif_list,args.input_metadata_file,args.output_dir)