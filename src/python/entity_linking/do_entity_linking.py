'''
This implementation of entity-linking was done for WM hackathon. It may be outdated given that we now have a better
implementation of entity-linking within jsonld_serializer. Nonetheless, this is currently the script being called
by nn_edl stage of the sequence (causeex_pipeline.pl).
- Note that the ontology and vector_utils modules used in this implementation are different from the ones used by jsonld_serializer
-  See the following commits for details: d24cbe0dde463b47153e22f31c22668d62ca996b, f172bcbe8b043a1f6b864f4262159a43da7b222c
'''

import sys, os
from vector_utils import read_embeddings, get_vector_similarity, compute_average_vector
from ontology import read_ontology
from collections import defaultdict, OrderedDict
import yaml
import re



global artifact_type
global similarity_threshold


def get_similarity_rows(names, name_types, name_embeddings, type_embeddings, concept_embeddings):
    name_similarity_rows = []
    type_similarity_rows = []
    for i in range(len(names)):
        name = names[i]
        type = name_types[i]
        name_vector = name_embeddings[i]
        type_vector = type_embeddings[i]

        def do_linking(artifact, artifact_embedding, similarity_rows):
            similarity_row = []
            if artifact in concept_embeddings.keys():
                for concept_path, concept_embedding in concept_embeddings[artifact]:
                    score = get_vector_similarity(artifact_embedding,concept_embedding)
                    similarity_row.append((concept_path,score))
                # sort similarity_row
                similarity_row = sorted(similarity_row,key=lambda x:x[1],reverse=True)
            similarity_rows.append(similarity_row)

        # do type linking
        do_linking(type,type_vector,type_similarity_rows)
        # do entity linking
        do_linking(name,name_vector,name_similarity_rows)

    return name_similarity_rows, type_similarity_rows

def main():
    serif_instances_file = sys.argv[1]
    type_predictions_file = sys.argv[2]
    ontology_file = sys.argv[3]
    ontology_name = "BBN_HUME" # hard-coding for now
    type_output_file = sys.argv[4]
    name_output_file = sys.argv[5]
    # hard-coding the following for now
    embeddings_file = '/nfs/raid87/u14/learnit_similarity_data/glove_6B_50d_embeddings/glove.6B.50d.p'
    
    # read ontology
    ontology_dict = read_ontology(ontology_file)

    names = []  # list of names
    name_types = []  # list of predicted types for each name
    with open(serif_instances_file) as serif_file:
        for line in serif_file:
            fields = line.split('\t')
            st = int(fields[0])
            end = int(fields[1])
            tokens = fields[2].lower().split()
            name = ' '.join(tokens[st:end]).lower()
            names.append(name)
    if len(names)==0:
        return

    with open(type_predictions_file) as type_file:
        for line in type_file:
            type = line.split('\t')[1][:-1].lower()
            type = re.sub("[\\s_]+"," ",type)
            name_types.append(type)

    # read embeddings
    print 'Reading the embeddings file...'
    embeddings = read_embeddings(embeddings_file)
    print 'Read '+str(len(embeddings))+' embeddings...'

    concept_embeddings = defaultdict(list)
    # maps a word to a list of vectors; each vector is for a particular ontological xpath
    for concept in ontology_dict:
        if concept.endswith("_source") or concept.endswith("_description"):
            continue
        for xpath in ontology_dict[concept]:
            xpath = xpath.replace("wikidata.","").replace("/_source/","/").replace("/_description/","/")
            all_concepts = [c.lower() for c in re.split("[/\\s_]",xpath) if c]
            vector = compute_average_vector(all_concepts,embeddings)
            normalized_concept = concept.replace("wikidata.","").replace("/_source/","/").replace("/_description/","/").replace("_"," ").lower()
            concept_embeddings[normalized_concept].append((xpath,vector))

    name_embeddings = []  # list of embeddings for each name
    type_embeddings = [] # list of embeddings for each type (in the same order as names)

    for i in range(len(names)):
        name = names[i]
        type = name_types[i]
        name_embeddings.append(compute_average_vector(name.split(),embeddings))
        type_embeddings.append(compute_average_vector(type.split(),embeddings))

    [name_similarities, type_similarities] = get_similarity_rows(names, name_types, name_embeddings,
                                                                  type_embeddings,concept_embeddings)

    def write_output(output_file,similarity_rows):
        with open(output_file,'w') as fp:
          for i in range(len(similarity_rows)):
            out_fields = [ontology_name]
            sim_row = similarity_rows[i]
            out_fields.extend([str(i) for w_s in sim_row for i in w_s])
            fp.write('\t'.join(out_fields)+'\n')

    write_output(type_output_file,type_similarities)
    write_output(name_output_file,name_similarities)

    print "Type linking output written to: "+type_output_file
    print "Entity linking output written to: "+name_output_file
                
    print 'Done!'

if __name__ == '__main__':
    main()
