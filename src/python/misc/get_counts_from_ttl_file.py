import sys, os, re

entity_re = re.compile("bbnta1:\w\w\w-[\w_]+ a ")
causal_re = re.compile("bbnta1:REL-CausalAssertion-\S+ a causal:CausalAssertion")
event_re = re.compile("bbnta1:EV-\S+ a event") # includes both event:Event and event-hierarchy:*
generic_event_re = re.compile("bbnta1:EV-\S+ a event:Event")

if len(sys.argv) != 2:
    print "Usage: input-file"
    sys.exit(1)

input_file = sys.argv[1]
i = open(input_file, 'r')

entity_count = 0
casual_assertion_count = 0
event_count = 0
generic_event_count = 0

for line in i:
    if entity_re.match(line):
        entity_count += 1
    if causal_re.match(line):
        casual_assertion_count += 1
    if event_re.match(line):
        event_count += 1
    if generic_event_re.match(line):
        generic_event_count += 1

i.close()

print "Entity count: " + str(entity_count)
print "Causal assertion count: " + str(casual_assertion_count)
print "Event count (incl. generic): " + str(event_count)
print "Generic event count: "+ str(generic_event_count)
