import codecs
import json
import os
import sys
from collections import defaultdict

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_dir, "..", "knowledge_base"))
try:
    from internal_ontology import Ontology
    from internal_ontology import OntologyMapper
except ImportError as e:
    raise e

predictions_json = sys.argv[1]
ontology_yaml = sys.argv[2]
ontology_flag = sys.argv[3]

ontology_mapper = OntologyMapper()
ontology_mapper.load_ontology(ontology_yaml)
mapped_predictions = dict()

with codecs.open(predictions_json, 'r', encoding='utf8') as f:
    predictions = json.load(f)

for nn_type, doc_and_sent_to_output in predictions.items():
    sources = ontology_mapper.look_up_external_types(nn_type, ontology_flag)

    if len(sources) > 1:  # TODO
        msg = "Multiple sources have been mapped to this internal type. "
        msg += "This is allowed but not implemented for this script.  @criley"
        raise NotImplementedError(msg)
        # for source in sources...

    if len(sources) < 1:
        continue

    source = sources[0]
    mapped_predictions.setdefault(source, {})
    for doc_and_sent, output in doc_and_sent_to_output.items():
        if doc_and_sent not in mapped_predictions[source]:
            output["eventType"] = source
            mapped_predictions[source][doc_and_sent] = output
        else:  # smart (we hope) overwrite
            best_score = float(
                mapped_predictions[source][doc_and_sent]["score"])
            if float(output["score"]) > best_score:
                output["eventType"] = source
                mapped_predictions[source][doc_and_sent] = output

with codecs.open(predictions_json + ".mapped", 'w', encoding='utf8') as f:
    json.dump(mapped_predictions, f)
