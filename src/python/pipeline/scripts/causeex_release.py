import sys, os, time

def line_count(fl):
    with open(fl) as f:
        for i, l in enumerate(f):
            pass
        return i + 1

if len(sys.argv) != 3:
    print "Usage: " + sys.argv[0] + " input_serialization_dir release_dir"
    sys.exit(1)

FILE_SIZE_LIMIT = 2000000000

input_dir, master_output_dir = sys.argv[1:]
input_dir = os.path.realpath(input_dir)
document_type = os.path.basename(input_dir)

output_dir = os.path.join(master_output_dir, document_type)
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

for filename in os.listdir(input_dir):
    if not filename.endswith(".nt"):
        continue
    
    input_nt_file = os.path.join(input_dir, filename)
    output_prefix = os.path.join(output_dir, document_type + "_triples_")
    file_size = os.path.getsize(input_nt_file)
    num_splits = file_size / FILE_SIZE_LIMIT + 1
    line_count = line_count(input_nt_file)
    lines_per_split = line_count / num_splits + 1
    
    cmd = "split -l " + str(lines_per_split) + " -d -a 2 " + input_nt_file + " " + output_prefix
    print cmd
    os.system(cmd)

    for output_filename in os.listdir(output_dir):
        output_file = os.path.join(output_dir, output_filename)
        os.rename(output_file, output_file + ".nt")

    break # assumes one .nt file in directory

