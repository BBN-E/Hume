import sys, os, codecs, re, json
from datetime import datetime

sys.path.append("/nfs/ld100/u10/bmin/repositories/svn/TextGroup/Active/Projects/SERIF/python/")
# sys.path.append(os.path.join('/nfs/raid84/u12/ychan/Active/Projects', 'SERIF', 'python'))
import json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

event_mention_to_embeddings = {}

def sanitize_triple(em):
    triger = em[0]
    sentence = em[1]
    return triger.strip().replace("\t", " ").replace(" ", "_") + "||" + sentence.strip().replace("\t", " ").replace(" ", "_")

def calculate_similarity(file_vacob, file_sim):
    fp_vacob = open(file_vacob, "w")
    fp_sim = open(file_sim, "w")

    # Get embeddings for all the query rels
    NUM_DIM = 768

    query_embs = np.zeros([len(event_mention_to_embeddings.keys()), NUM_DIM])

    idx = 0
    array_em = []
    for em in event_mention_to_embeddings:
        vec = event_mention_to_embeddings[em]
        query_embs[idx, :] = vec
        array_em.append(em)
        idx += 1

    # Compute cosine similarity between each EM and every other
    sims = cosine_similarity(query_embs)

    # Format and write out the results
    for k in range(len(array_em)):
        em1 = array_em[k]
        fp_vacob.write(sanitize_triple(em1) + "\n")
        for i in range(sims.shape[0]):
            cos_dist = sims[k, i]
            em2 = array_em[i]

            print("SIM\t" + str(cos_dist) + "\t" + str(em1[0]) + "\t" + str(em2[0]) + "\t" + str(em1) + "\t" + str(em2))

            fp_sim.write(sanitize_triple(em1) + " " + sanitize_triple(em2) + " " + str(cos_dist) +"\n")

    #for em1 in event_mention_to_embeddings:
    #    for em2 in event_mention_to_embeddings:
    #        sim = cosine_similarity(event_mention_to_embeddings[em1].reshape(-1, 1), event_mention_to_embeddings[em2].reshape(-1, 1))
    #        print("SIM\t" + str(sim) + "\t" + str(em1[0]) + "\t" + str(em2[0]) + "\t" + str(em1) + "\t" + str(em2))

    fp_vacob.close()
    fp_sim.close()

def read(jsonl):
    cur_trigger = None
    cur_tokens = None
    cur_array_emb = None

    with open(jsonl) as fp:
        line = fp.readline().strip()

        linex_index, array_token, array_embed = parse_json(line)
        if linex_index==None or array_token==None or array_embed==None:
            return

        if linex_index%3==1:
            cur_trigger = array_token[1:-1]
        if linex_index%3==2:
            cur_tokens = array_token
            emb = get_trigger_emb(cur_trigger, cur_tokens, array_embed)

            event_mention = (' '.join(cur_trigger), ' '.join(array_token[1:-1]))
            event_mention_to_embeddings[event_mention] = emb
            print(str(event_mention) + "\t" + str(emb))
        cnt = 1
        while line:
            #print("Line {}: {}\n".format(cnt, line.strip()))
            line = fp.readline().strip()

            linex_index, array_token, array_embed = parse_json(line)
            if linex_index == None or array_token == None or array_embed == None:
                continue

            if linex_index % 3 == 1:
                cur_trigger = array_token[1:-1]
            if linex_index % 3 == 2:
                cur_tokens = array_token
                emb = get_trigger_emb(cur_trigger, cur_tokens, array_embed)

                event_mention = (' '.join(cur_trigger), ' '.join(array_token[1:-1]))
                event_mention_to_embeddings[event_mention] = emb
                print(str(event_mention) + "\t" + str(len(emb)) + "\t" + str(emb))

            cnt += 1

def get_trigger_emb(trigger, array_token, array_embed):
    for i in range(0, len(array_token)):
        matched = True
        for j in range(0,len(trigger)):
            if array_token[i+j]!=trigger[j]:
                matched = False
        if matched:
            return array_embed[i+len(trigger)-1]

    return None

#    idx=0
#    for sentence_token in array_token:
#        matched=True
#        for trigger_token in trigger:
#            if sentence_token!=trigger_token:
#                matched=False
#        if matched:
#            return array_embed[idx+len(trigger)-1]
#        idx+=1
#    return None

def parse_json(line):
    try:
        j = json.loads(line)
    except:
        return None, None, None

    linex_index = j['linex_index']
    features = j['features']
    array_token = []
    array_embed = []
    for feature in features:
        token = feature['token']
        array_token.append(token)

        layers = feature['layers']
        for layer in layers:
            index = layer['index']
            values = layer['values']

            if index==-1:
                array_embed.append(values)

    return linex_index, array_token, array_embed

if __name__ == "__main__":
    jsonl="/nfs/raid88/u10/users/bmin/experiments/bert/test.json.jsonl"

    file_vacob="/nfs/raid88/u10/users/bmin/experiments/bert/test.em.vocab"
    file_sim="/nfs/raid88/u10/users/bmin/experiments/bert/test.em.sim"

    read(jsonl)
    calculate_similarity(file_vacob, file_sim)

    #m1=[0.1, 0,2, -0,3]
    #m2=[0.3, -0.1, 0.2]
    #print(cosine_similarity(np.asarray(m1), np.asarray(m2)))


