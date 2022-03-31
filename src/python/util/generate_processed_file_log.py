import os,json


def main():
    kafka_message_root = "/home/hqiu/tmp/dart.031522"
    processed_doc_ids = set()
    for ontology_id in os.listdir(kafka_message_root):
        for doc_uuid_p in os.listdir(os.path.join(kafka_message_root, ontology_id)):
            doc_uuid = doc_uuid_p[:-len(".txt")]
            processed_doc_ids.add((doc_uuid, ontology_id))

    with open("/home/hqiu/tmp/processed2.log",'w') as wfp:
        for doc_uuid, ontology_id in processed_doc_ids:
            wfp.write("{}\t{}\n".format(doc_uuid,ontology_id))


if __name__ == "__main__":
    main()