
import os

def create_file_name_to_path(file_list, extension):
    docid_to_path = dict()
    with open(file_list) as fp:
        for i in fp:
            i = i.strip()
            docid = os.path.basename(i).replace(extension, "")
            docid_to_path[docid] = i
    return docid_to_path