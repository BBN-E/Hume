# Sample call:
#  python /nfs/raid66/u14/users/azamania/git/Hume/src/python/util/convert_collab2_cdr_to_sgm.py /nfs/raid87/u11/CauseEx_Datasets/Collab2/cdr/m24-shaved-dataset /nfs/raid87/u11/CauseEx_Datasets/Collab2/sgm/m24-shaved-dataset /nfs/raid87/u11/CauseEx_Datasets/Collab2/metadata_files/metadata-m24-shaved-dataset.txt /nfs/raid87/u11/CauseEx_Datasets/Collab2/batch_files/m24-shaved-dataset.list

import sys, os, codecs, json, shutil, datetime
from random import shuffle

reload(sys)
sys.setdefaultencoding('utf8')
# character that serif doesn't like: 
# Unexpected Input Exception: Invalid Unicode wide character
bad_characters = { (237, 160, 189,), (237, 180, 146,), (237, 160, 190,), (237, 182, 129,), 
                   # The following are new based on COLLAB2 set:
                   (237, 160, 188,), (237, 183, 183,), 
                   (237, 160, 181,), (237, 177, 159,), 
                   }


def is_good_break_point(char_pos, len_utext, utext):
    if char_pos > len_utext - 10000:
        return False
    if utext[char_pos] != "\n" or utext[char_pos+1] != "\n":
        return False

    return True

# character that python considers UTF-8, but Serif doesn't like
def is_bad_character(c, filename):
    bytes = c.encode(encoding='utf8')
    if len(bytes) < 3:
        return False
    key = (ord(bytes[0]), ord(bytes[1]), ord(bytes[2]),)
    if key in bad_characters:
        #print "Skipping character in " + filename
        return True
    return False

# Returns list of strings
def split_article_text(doc_info):
    #return ["TEST"]

    char_pos = 0
    char_count = 0
    current_doc_text = ""
    split_documents = []
    contents = ""
    if "extracted_text" in doc_info:
        contents = doc_info["extracted_text"]

    len_contents = len(contents)
    
    # Sanity check
    try:
        byte_string = contents.encode('utf8')
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    for c in contents:
        if not is_bad_character(c, doc_info["source_uri"]):
            current_doc_text += c
        else:
            current_doc_text += " "

        if char_count > 50000 and is_good_break_point(char_pos, len_contents, contents):
            split_documents.append(current_doc_text)
            current_doc_text = ""
            char_count = 0
        char_count += 1
        char_pos += 1

    split_documents.append(current_doc_text)
    return split_documents

def get_8_digit_doc_date(doc_info):
    # assumes only news stories has good dates
    #if doc_info["source_uri"].find(".html") == -1:
    #    return "NODATE"
    
    if doc_info["extracted_metadata"].get("CreationDate", None) is None:
        return "NODATE"
    timestamp = doc_info["extracted_metadata"]["CreationDate"]
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y%m%d")

def get_docid(doc_info, count, dataset_tag):
    return "ENG_NW_" + get_8_digit_doc_date(doc_info) + "_" + dataset_tag + "_" + str(count).zfill(5)

def get_document_type(doc_info):
    uri = doc_info["source_uri"]
    if uri.startswith("AllAfrica Data/"):
        return "news"
    if uri.startswith("Intel Reports/"):
        return "intel"
    if uri.startswith("Strategic Guidance"):
        return "strategicguidance"
    if uri.startswith("Abstracts/"):
        return "abstract"
    if uri.startswith("Unstructured Data/"):
        return "analytic"
    if uri.startswith("Unstructured-EMMNews/"):
        return "news"
    if uri.startswith("Unstructured/"):
        return "analytic"
    if uri.startswith("Intell/"):
        return "intel"
    if uri.startswith("News/"):
        return "news"
    if uri.startswith("Relations/"):
        return "analytic"
    if uri.startswith("Academic/"):
        return "analytic"
    if uri.startswith("Associations/"):
        return "analytic"
    if uri.startswith("Country Specific Programs/"):
        return "analytic"
    if uri.startswith("Mission Analysis Initial Docs/"):
        return "analytic"
    if uri.startswith("Treaties/"):
        return "analytic"
    if uri.startswith("US Strategic Guidance/"):
        return "strategicguidance"
    if uri.startswith("Seneario_Analysis/"):
        return "analytic"
    if doc_info["extracted_ntriples"].find("DataProvenance#Unstructured") != -1:
        return "analytic"
    print("Could not find document type for: " + uri)
    sys.exit(1)

def clean_article_text(article_text):
    article_text = article_text.replace("<", " ")
    article_text = article_text.replace(">", " ")
    return article_text

def write_document(docid, doc_info, article_text, output_dir, metadata_stream, sgm_file_list, offset, input_dir, input_file, document_type):
    article_text = clean_article_text(article_text)
    date_str = get_8_digit_doc_date(doc_info)

    f = os.path.join(output_dir, docid + ".sgm")
    o = codecs.open(f, 'w', encoding='utf8')

    header = '<DOC id="' + docid + '">\n'
    
    if date_str != "NODATE":
        header += '<DATETIME> ' + date_str + ' </DATETIME>\n'

    header += '<TEXT>\n'
    o.write(header)

    # offset is what we have to add to Serif offsets to get offsets into original json extracted_text
    offset -= len(header) 

    o.write(article_text)
    o.write('\n</TEXT>')
    o.write('\n</DOC>\n')
    o.close()

    sgm_file_list.append(f)

    # Handle metadata
    metadata_date_str = "UNKNOWN"
    if date_str != "NODATE":
        metadata_date_str = date_str
    reliability = "1.0"
    author = "UNKNOWN"
    if "Author" in doc_info["extracted_metadata"]:
        author = doc_info["extracted_metadata"]["Author"].replace("\t", " ")
    url = "UNKNOWN"
    if "URL" in doc_info["extracted_metadata"]:
        url = doc_info["extracted_metadata"]["URL"]

    cdr_file_path = os.path.abspath(input_dir) + "/" + doc_info["source_uri"] + ".cdr"
    if not os.path.exists(cdr_file_path):
        cdr_file_path = input_file
    if not os.path.exists(cdr_file_path):
        print("Error: Could not get full path of file to write to metadata file: " + cdr_file_path)
        sys.exit(1)
    metadata_stream.write(docid + "\t" + 
                          cdr_file_path + "\t" +
                          metadata_date_str + "\t" +
                          reliability + "\t" + 
                          document_type + "\t" +
                          os.path.relpath(f,os.path.join(output_dir,os.path.pardir,os.path.pardir)) + "\t" +
                          doc_info["document_id"] + "\t" +
                          str(offset) + "\t" +
                          author + "\t" +
                          url + "\n"
                          )

    offset += len(header)
    offset += len(article_text)

    return offset

if len(sys.argv) != 5:
    print("Usage: " + sys.argv[0] + " input-dir output-sgm-dir output-metadata-file output-sgm-list-file")
    sys.exit(1)

input_dir, output_dir, metadata_file, sgm_list_file = sys.argv[1:]

m = codecs.open(metadata_file, 'w', encoding='utf8')
s = codecs.open(sgm_list_file, 'w', encoding='utf8')
sgm_file_locations = []

document_count = 0 # change if you want to start at a higher docid counter, like if you have supplimental .cdr files
dataset_tag = "COLLAB2"
document_type_count = 0
documents_in_current_document_type = 0

if os.path.isdir(output_dir):
    shutil.rmtree(output_dir)
    os.makedirs(output_dir)

filenames = os.listdir(input_dir)
for filename in filenames:
    if not filename.endswith(".cdr"):
        continue
    
    input_file = os.path.join(input_dir, filename)
    
    i = codecs.open(input_file, 'r', encoding='utf8')
    contents = i.read()
    i.close()
    doc_info = json.loads(contents)
    
    if documents_in_current_document_type >= 50:
        document_type_count += 1
        documents_in_current_document_type = 0

    document_type = "COLLAB2_" + str(document_type_count)

    offset = 0
    splits = 0
    for article_text in split_article_text(doc_info):
        splits += 1
        docid = get_docid(doc_info, document_count, dataset_tag)
        document_count += 1
        offset = write_document(docid, doc_info, article_text, output_dir, m, sgm_file_locations, offset, os.path.dirname(input_dir), input_file, document_type)
    documents_in_current_document_type += splits

shuffle(sgm_file_locations)
for sgm_file in sgm_file_locations:
    s.write(sgm_file + "\n")

m.close()
s.close()

