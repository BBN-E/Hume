#!/bin/bash

bin=+JSERIF_ROOT+/serif-util/target/appassembler/bin/AddEventMentionFromOffsets

learnit_json_causal_relations=+learnit_json_causal_relations+
serif_json_causal_relations_dir=+serif_json_causal_relations_dir+
strListSerifXmlFiles=+input_serifxmls+
strOutputDir=+output_serifxml_dir+
MIN_FREQ_EVENT_PAIRS=+MIN_FREQ_EVENT_PAIRS+
strFileTripleRelationEventPairs=+str_file_triple_relation_event_pairs+


$bin $learnit_json_causal_relations $serif_json_causal_relations_dir $strListSerifXmlFiles $strOutputDir $MIN_FREQ_EVENT_PAIRS $strFileTripleRelationEventPairs

