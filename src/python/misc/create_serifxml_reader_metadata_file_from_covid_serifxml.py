import sys, os, re, serifxml3

date_re = re.compile(r"(\d\d\d\d)-(\d\d)-(\d\d)")

def get_date_created(doc):
    date_string = doc.document_time_start 
    m = date_re.match(date_string)
    if m is None:
        return "UNKNOWN"
    return m.group(1) + m.group(2) + m.group(3)

if len(sys.argv) != 3:
    print("Usage input-serifxml-list output-metadata-file")
    sys.exit(1)

input_file, output_file = sys.argv[1:]

i = open(input_file)
o = open(output_file, 'w')
for line in i:
    line = line.strip()
    serif_doc = serifxml3.Document(line)

    docid = serif_doc.docid
    source = "COVID Dataset"
    date_created = get_date_created(serif_doc)
    credibility = 1.0
    doc_type = "news"
    filename = docid
    uuid = docid
    
    o.write(docid + "\t" + source + "\t" + date_created + "\t" + str(credibility) + "\t" + doc_type + "\t" + filename + "\t" + uuid + "\n")
o.close()
