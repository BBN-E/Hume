import sys, os, codecs, shutil

if len(sys.argv) != 4 and len(sys.argv) != 5:
    print "Usage input-dir output-dir metadata-file [max_files_per_directory]"
    sys.exit(1)

input_serifxml_list = sys.argv[1]
output_dir = sys.argv[2]
metadata_file = sys.argv[3]

max_files_per_directory = None
if len(sys.argv) == 5:
    max_files_per_directory = int(sys.argv[4])

document_types = dict()
document_type_to_file_count = dict()
document_type_to_dir_count = dict()

o = codecs.open(metadata_file, 'r', encoding='utf8')
for line in o:
    line = line.strip()
    pieces = line.split("\t")
    docid = pieces[0]
    document_type = pieces[4]
    document_types[docid] = document_type
o.close()

i = open(input_serifxml_list)

for line in i:
    line = line.strip()
    filename = os.path.basename(line)
    docid = filename
    if filename.endswith(".serifxml"):
        docid = filename[0:-(len(".serifxml"))]
    elif filename.endswith(".xml"):
        docid = filename[0:-(len(".xml"))]
    filepath = line
    document_type = document_types[docid]
    output_path = os.path.join(output_dir, document_type)
    if max_files_per_directory is not None:
        if document_type not in document_type_to_file_count:
            document_type_to_file_count[document_type] = 0
        if document_type not in document_type_to_dir_count:
            document_type_to_dir_count[document_type] = 0
        
        modified_max_files_per_directory = max_files_per_directory
        if document_type == "analytic": # these tend to be large
            modified_max_files_per_directory = max(modified_max_files_per_directory / 2, 1)
        if document_type_to_file_count[document_type] >= modified_max_files_per_directory:
            document_type_to_file_count[document_type] = 0
            document_type_to_dir_count[document_type] += 1

        document_type_to_file_count[document_type] += 1
        output_path = os.path.join(output_dir, document_type + "_" + str(document_type_to_dir_count[document_type]))

    if not os.path.isdir(output_path):
        os.makedirs(output_path)

    shutil.copy(filepath, output_path)

i.close()
