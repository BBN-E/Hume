# The jserif program SerifXMLEDLUpdater requires entity linking information
# in addition to new mentions and entity. But for causeex_pipeline, we 
# don't want to use any entity linking info, so this script essentially 
# creates empty entity linking files to give to SerifXMLEDLUpdater. 

import sys, os

if len(sys.argv) != 4:
    print "Usage: " + sys.argv[0] + " input-instances-file type-linking-output-file entity-linking-output-file"
    sys.exit(1)

input_file, type_linking_file, entity_linking_file = sys.argv[1:]

i = open(input_file)
o1 = open(type_linking_file, 'w')
o2 = open(entity_linking_file, 'w')

for line in i:
    pieces = line.split("\t")
    o1.write("BBN_HUME\t" + pieces[3] + "\n")  # pieces[3] is entity type
    o2.write("BBN_HUME\n")

i.close()
o1.close()
o2.close()
