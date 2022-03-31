import re,datetime,sys

def read_metadata_file(metadata_file):
    docid_to_document_properties = dict()
    with open(metadata_file, 'r') as m:
        for line in m:
            pieces = line.strip().split("\t")
            document_properties = dict()
            docid = pieces[0]
            document_properties["docid"] = docid
            document_properties["doc_type"] = pieces[4].strip()
            document_properties["source"] = re.sub("^\./", "", re.sub("\n", " ", pieces[1]))
            document_properties["uuid"] = pieces[6]
            document_properties["filename"] = re.sub("\n", " ", pieces[5])
            document_properties["credibility"] = float(pieces[3])
            date_created_str = pieces[2]
            if date_created_str != "UNKNOWN":
                document_properties["date_created"] = datetime.datetime.strptime(date_created_str, "%Y%m%d")
            else:
                document_properties["date_created"] = "UNKNOWN"
            document_properties["offset"] = 0
            if len(pieces) > 7:
                document_properties["offset"] = int(pieces[7])
            document_properties["author"] = "UNKNOWN"
            if len(pieces) > 8:
                document_properties["author"] = pieces[8]
            document_properties["online_source"] = "UNKNOWN"
            if len(pieces) > 9:
                document_properties["online_source"] = pieces[9]
            if len(pieces) > 10:
                print("Too many pieces")
                sys.exit(1)
            docid_to_document_properties[docid] = document_properties
    return docid_to_document_properties

def main():
    cord_19_metadata = "/nfs/raid88/u10/users/hqiu/raw_corpus/cord_19.111420/metadata.txt"
    aylien_metadata = "/nfs/raid88/u10/users/hqiu/raw_corpus/aylien_covid19/metadata.txt"

    doc_id_to_cord19 = read_metadata_file(cord_19_metadata)
    doc_id_to_aylien = read_metadata_file(aylien_metadata)
    # How many articles each

    doc_uuid_cord19 = set()
    doc_uuid_aylien = set()
    date_to_cnt = dict()


    for doc_id,entry in doc_id_to_cord19.items():
        doc_uuid_cord19.add(entry['uuid'])
    for doc_id,entry in doc_id_to_aylien.items():
        doc_uuid_aylien.add(entry['uuid'])
        if entry['date_created'] != "UNKNOWN":
            date_to_cnt[(entry['date_created'].year,entry['date_created'].month)] = date_to_cnt.get((entry['date_created'].year,entry['date_created'].month),0)+1
    # Aylien How many in 01/20-05/20

    print("Num of docs in cord19: {}".format(len(doc_uuid_cord19)))
    print("Num of docs in aylien: {}".format(len(doc_uuid_aylien)))
    for (year,month),cnt in date_to_cnt.items():
        print("{}/{}: {}".format(month,year,cnt))

if __name__ == "__main__":
    main()