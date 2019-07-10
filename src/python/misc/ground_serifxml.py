
import os
import sys
import argparse
import json
import io
from collections import defaultdict

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.abspath(__file__), "..", "..", "knowledge_base")))
sys.path.insert(0, os.path.join(os.environ['SVN_PROJECT_ROOT'], 'SERIF', 'python'))

from internal_ontology.internal_ontology import InternalOntology
from elements.kb_event_mention import KBEventMention as EM
import serifxml


counter = defaultdict(int)


def validate_config(config_path):
    if not os.path.exists(config_path):
        raise IOError("Must provide a valid file to ground_serifxml.py")
    args = {}
    with open(config_path, 'r') as config_file:
        for line in config_file:
            k, v = line.split(': ')
            args[k] = v.strip()
    grounder_args = []
    grounding_call_args = []
    arguments = ['event_ontology_file', 'examples_json', 'embeddings_file',
                 'lemma_file', 'stopword_file']
    for k in arguments:
        if k not in args:
            raise IOError('Config file missing InternalOntology argument `'
                          '{}`'.format(k))
        grounder_args.append(args.pop(k))
    if 'ontology_flag' not in args:
        raise IOError('Config file missing grounding call argument '
                      '`ontology_flag`')
    grounding_call_args.append(args.pop('ontology_flag'))
    if 'n_best' not in args:
        raise IOError('Config file missing grounding call argument `n_best`')
    grounding_call_args.append(int(args.pop('n_best')))
    if 'threshold' not in args:
        raise IOError('Config file missing grounding call argument `threshold`')
    grounding_call_args.append(float(args.pop('threshold')))
    return grounder_args, grounding_call_args


def get_grounder(grounder_args):
    grounder = InternalOntology(*grounder_args)
    return grounder


def read_serifxml_event_mentions(serifxml_path):
    global counter
    if not os.path.exists(serifxml_path):
        raise IOError("Must provide a SERIF .xml file to ground_serifxml.py")
    mentions = []
    serif_doc = serifxml.Document(serifxml_path)
    docid = serif_doc.docid
    for sentence in serif_doc.sentences:
        for event_mention in sentence.event_mention_set:
            event_type = unicode(event_mention.event_type)
            original_score = event_mention.score
            anchor = event_mention.anchor_node
            anchor_string = u" ".join([unicode(token.text) for token in anchor.tokens])
            event_mention = EM(
                "~", None, event_type, anchor_string, 1, 2, "", None, [], None,
                confidence=original_score)
            mentions.append(event_mention)
            event_type = u"Event" if event_type == u"Generic" else event_type
            counter[(event_type, anchor_string)] += 1
    return docid, mentions


def ground_event_mention(internal_ont_grounder, grounding_args, event_mention):
    cache_key, grounded_classes = internal_ont_grounder.\
        ground_event_mention_to_external_ontology_by_similarity(event_mention,
                                                                *grounding_args)
    return cache_key, grounded_classes


def cache_serifxmls(serifxmls_path, grounder, call_args):
    cache = {}
    if os.path.isdir(serifxmls_path):
        serifxmls = [f for f in os.listdir(serifxmls_path)
                     if f.endswith('xml') and os.path.isfile(f)]
    else:
        with io.open(serifxmls_path, 'r') as f:
            serifxmls = [line.strip() for line in f.readlines()]
    for serifxml in serifxmls:
        docid, mentions = read_serifxml_event_mentions(serifxml)
        # "grounding cache" format
        for mention in mentions:
            key, groundings = ground_event_mention(grounder, call_args, mention)

            # Original class isn't part of internal ontology!  report.
            if groundings is None:
                print "WARNING: ungroundable type: {}".format(key.split('|||')[1])
                #cache[key] = [(key.split('|||')[1], mention.confidence)]
                groundings = []

            # No grounding similarity score exceeded threshold: Keep original
            if len(groundings) == 0:
                original_type = grounder.get_grounding_candidate(mention)[1]
                original_score = mention.confidence
                groundings.append((original_type, original_score))
            cache[key] = groundings
    return cache


def main():
    global counter
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--event_ontology")
    arg_parser.add_argument("--exemplars")
    arg_parser.add_argument("--embeddings")
    arg_parser.add_argument("--lemmas")
    arg_parser.add_argument("--stopwords")
    arg_parser.add_argument("--which_ontology")
    arg_parser.add_argument("--threshold", type=float)
    arg_parser.add_argument("--serifxmls")
    arg_parser.add_argument('--output', nargs='?', default=None)
    args = arg_parser.parse_args()

    grounder_args = [args.event_ontology,
                     args.exemplars,
                     args.embeddings,
                     args.lemmas,
                     args.stopwords]
    grounding_call_args = [args.which_ontology, 5, args.threshold]

    grounder = get_grounder(grounder_args)
    cache = cache_serifxmls(args.serifxmls, grounder, grounding_call_args)
    print json.dumps(cache, indent=4, sort_keys=True)
    if args.output is not None:
        with io.open(args.output, 'w', encoding='utf8') as f:
            f.write(unicode(json.dumps(cache, ensure_ascii=False,indent=4,sort_keys=True)))
        with io.open(args.output + '.frequencies', 'w', encoding='utf8') as f:
            for pair, freq in sorted(counter.items(), reverse=True, key=lambda x: x[1]):
                f.write(u"{}\t{}\t{}\n".format(freq, pair[0], pair[1]))
                for grounding, score in cache.get(u'|||'.join([u"Event", pair[0], pair[1]]), []):
                    f.write(u'\t{}\t{}\n'.format(grounding, score))


if __name__ == "__main__":
    main()
