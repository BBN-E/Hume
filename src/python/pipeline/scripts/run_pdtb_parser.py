import sys, os, json, codecs, subprocess, time

if "SVN_PROJECT_ROOT" not in os.environ:
    print "Need to set environment variable SVN_PROJECT_ROOT to access serifxml.py library"
    sys.exit(1)

sys.path.append(os.path.join(os.environ["SVN_PROJECT_ROOT"], "SERIF", "python"))
import serifxml

if len(sys.argv) != 8:
    print "Usage: input-serifxml-file master-output-dir metadata-dir dir-name config-dir parser-jar memory-limit-gb"
    sys.exit(1)

input_file, master_output_dir, metadata_dir, dir_name, config_dir, parser_jar, memory_limit_gb = sys.argv[1:]
safe_memory_limit_gb = int(memory_limit_gb) - 1

output_dir = os.path.join(master_output_dir, dir_name)
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

basename = os.path.basename(input_file)
if basename.endswith(".xml"):
    basename = basename[0:-4]

# CREATE INPUT TEXT FILE

# Text file containing sentences that we will run on
text_filename = basename
if not text_filename.endswith(".txt"):
    text_filename = text_filename + ".txt"
outfile = os.path.join(output_dir, text_filename)
o = codecs.open(outfile, 'w', encoding='utf8')

# Metadata file containing char offset mapping from text file to
# serifxml file
metadata_filename = basename + ".meta"
metadata_file = os.path.join(metadata_dir, metadata_filename)
m = open(metadata_file, 'w')

document = serifxml.Document(input_file)
current_output_offset = 0
for sentence in document.sentences:
    original_sentence_text = sentence.text
    sentence_text = original_sentence_text.replace("\r", " ")
    sentence_text = sentence_text.replace("\n", " ")
    o.write(sentence_text + "\n")
    m.write(str(current_output_offset) + " " + str(sentence.start_char) + "\n")
    current_output_offset += len(sentence.text) + 1 # +1 for newline character
o.close()
m.close()

# RUN DISCOURSE PARSER

time_limit = 1800
os.chdir(config_dir)
memory_limit_parameter = "-Xmx" + str(safe_memory_limit_gb) + "G"
command = ["java", memory_limit_parameter, "-jar", parser_jar, output_dir]
print str(command)

proc = subprocess.Popen(command)

start_time = time.time()
while True:
    current_time = time.time()
    if current_time - start_time >= time_limit:
        proc.kill()
    poll = proc.poll()
    if poll is not None:
        # finished
        break

    time.sleep(5)

streamdata = proc.communicate()[0]
rc = proc.returncode

if rc != 0:
    # Failure, create empty output file
    final_output_dir = os.path.join(output_dir, "output")
    if not os.path.isdir(final_output_dir):
        os.makedirs(final_output_dir)
    empty_file = os.path.join(final_output_dir, basename + ".txt.pipe")
    o = open(empty_file, 'w')
    o.close()

    

