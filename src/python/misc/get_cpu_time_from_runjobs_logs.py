import sys, os, re

started_re = re.compile(r"Started at \w\w\w \w\w\w \d\d? (\d\d?):(\d\d):(\d\d)")
finished_re = re.compile(r"Finished at \w\w\w \w\w\w \d\d? (\d\d?):(\d\d):(\d\d)")

if len(sys.argv) != 3:
    print "Usage: " + sys.argv[0] + " input-logfile-dir output-file"
    sys.exit(1)

def convert(total_seconds):
    hours = total_seconds // 3600
    remainder = total_seconds - hours * 3600
    minutes = remainder // 60
    remainder = remainder - minutes * 60
    seconds = remainder

    return str(hours) + ":" + str(minutes).zfill(2) + ":" + str(seconds).zfill(2)

def process_file(f, component):
    global total_time 
    if not f.endswith(".log"):
        return
    i = open(f)
    contents = i.read()
    i.close()

    start_m = started_re.search(contents)
    end_m = finished_re.search(contents)

    if not start_m or not end_m:
        print "Couldn't find times in: " + f
        sys.exit(1)

    start_hours = int(start_m.group(1))
    end_hours = int(end_m.group(1))

    start_minutes = int(start_m.group(2))
    end_minutes = int(end_m.group(2))

    start_seconds = int(start_m.group(3))
    end_seconds = int(end_m.group(3))

    hours_delta = end_hours - start_hours
    if hours_delta < 0:
        hours_delta += 24 # Assumes everything takes < 24 hours

    minutes_delta = end_minutes - start_minutes
    if minutes_delta < 0:
        minutes_delta += 60
        hours_delta -= 1

    seconds_delta = end_seconds - start_seconds
    if seconds_delta < 0:
        seconds_delta += 60
        minutes_delta -= 1

    #o.write("difference_between: " + start_m.group(0) + " and " + end_m.group(0) + " is: " + str(hours_delta) + ":" + str(minutes_delta) + ":" + str(seconds_delta) + "\n")
    logfile_time = 3600 * hours_delta + 60 * minutes_delta + seconds_delta
        
    total_time += logfile_time
    if component not in components:
        components[component] = 0
    components[component] += logfile_time

def process_dir(d, component):
    for dirpath, dirnames, filenames in os.walk(d):
        for filename in filenames:
            process_file(os.path.join(dirpath, filename), component)

input_dir, output_file = sys.argv[1:]

total_time = 0 # in seconds
components = dict() # maps component name (e.g. serif) to total time in seconds

o = open(output_file, 'w')

filenames = os.listdir(input_dir)
for filename in filenames:
    path = os.path.join(input_dir, filename)
    if os.path.isdir(path):
        print filename
        component = filename
        if filename == "add_causal_factors":
            component = "learnit"
        process_dir(path, component)
    component = "misc"
    if filename == "causeex_pipeline-add_verbs_and_nouns_as_em.log":
        component = "learnit"
        
    process_file(path, component)

o.write("Total: " + convert(total_time) + "\n")
for component in components:
    o.write(component + ": " + convert(components[component]) + "\n")
        
o.close()


