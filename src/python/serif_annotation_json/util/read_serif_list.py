import os


def read_doc_list(path):
    doc_id_to_doc_path = dict()
    with open(path) as fp:
        for i in fp:
            i = i.strip()
            doc_id = os.path.basename(i)
            doc_id = doc_id.replace(".xml", "").replace(".serifxml", "").replace(".sgm", "")
            doc_id_to_doc_path[doc_id] = i
    return doc_id_to_doc_path


def read_doc_list_from_file_list_or_file_list_folder(serifxml_doc_list_file_or_folder):
    doc_id_to_doc_path = dict()

    if os.path.isdir(serifxml_doc_list_file_or_folder):
        for file in os.listdir(serifxml_doc_list_file_or_folder):
            d = read_doc_list(os.path.join(serifxml_doc_list_file_or_folder, file))
            doc_id_to_doc_path.update(d)
    else:
        d = read_doc_list(serifxml_doc_list_file_or_folder)
        doc_id_to_doc_path.update(d)

    return doc_id_to_doc_path
