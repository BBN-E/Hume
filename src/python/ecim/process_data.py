import os,sys,json,collections,datetime
from collections import defaultdict
from collections import Counter
import pickle
import pandas as pd

import tensorflow as tf
import numpy as np

NUM_MOST_COMMON_TRIGGER_PER_TYPE = 50
NUM_WORD_EMB_DIM = 100

def get_word(pos_and_word):
    items = pos_and_word.strip().split(":")
    return items[1]

def process_event_gigaword():
    input_text_file = "/nfs/raid88/u10/users/bmin/projects/events-socio-econ-indicators/gigaword-events/gigawordv5.full.events.txt"

    date2trigger_counter = defaultdict()

    with open(input_text_file,'r') as fp:
        for line in fp:
            line = line.strip()
            items = line.split("\t")
            year = int(items[2])
            month = int(items[3])
            day = int(items[4])
            trigger = get_word(items[5])

            date = '{:04d}-{:02d}-{:02d}'.format(year, month, day)

            # print (date + "\t" + trigger)

            if date not in date2trigger_counter:
                date2trigger_counter[date] = Counter()

            date2trigger_counter[date][trigger]+=1

    #for date, counter in date2trigger_counter.items():
        # counter = date2trigger_counter(date)
        # print (date + str(date2trigger_counter(date)))
        # sprint(date + "\t" + str(counter))

    # pickle.dump(date2trigger_counter, open("/nfs/raid88/u10/users/bmin/projects/events-socio-econ-indicators/gigaword-events/gigawordv5.full.events.txt.event_counts_by_date.p", "wb"))

    return date2trigger_counter

def process_vix_data():
    input_text_file = "/nfs/raid88/u10/users/bmin/projects/events-socio-econ-indicators/gigaword-events/VIX.txt"

    date2vix_vals = defaultdict()

    with open(input_text_file, 'r') as fp:
        for line in fp:
            line = line.strip()
            if line.startswith("#") or len(line)==0 or "n/a" in line:
                continue

            items = line.split("\t")

            print(line)
            date_string = items[0]

            fields = date_string.strip().split("/")
            year = int(fields[2])
            month = int(fields[0])
            day = int(fields[1])

            if year > 90:
                date = '19{:02d}-{:02d}-{:02d}'.format(year, month, day)
            elif year < 20:
                date = '20{:02d}-{:02d}-{:02d}'.format(year, month, day)

            vix = float(items[5])

            date2vix_vals[date] = vix

    #for date, val in date2vix_vals.items():
        # counter = date2trigger_counter(date)
        # print (date + str(date2trigger_counter(date)))
        #print(date + "\t" + str(val))

    # pickle.dump(date2vix_vals, open(
    #    "/nfs/raid88/u10/users/bmin/projects/events-socio-econ-indicators/gigaword-events/vix_by_date.p",
    #    "wb"))

    return date2vix_vals

# def generate_data_csv():
#     pickle_date2vix_vals = open("/nfs/raid88/u10/users/bmin/projects/events-socio-econ-indicators/gigaword-events/vix_by_date.p", "rb")
#     date2vix_vals = pickle.load(pickle_date2vix_vals)
#     pickle_date2trigger_counter = open("/nfs/raid88/u10/users/bmin/projects/events-socio-econ-indicators/gigaword-events/gigawordv5.full.events.txt.event_counts_by_date.p", "rb")
#     date2trigger_counter = pickle.load(pickle_date2trigger_counter)
#
#     # idx=0
#     # trigger2idx=dict()
#     # for date, counter in date2trigger_counter.items():
#     #     counter = date2trigger_counter[date]
#     #     for trigger in counter.keys():
#     #         if trigger not in trigger2idx:
#     #             trigger2idx[trigger] = idx
#     #             idx+=1
#
#     for date, val in date2vix_vals.items():
#         if date in date2trigger_counter:
#             trigger_counter = date2trigger_counter(date)



EMBEDDING_DIM = 100
GLOVE_PATH = f'/nfs/raid87/u10/shared/glove/glove.6B.100d.txt'
UNK_word = '<UNK>'

def load_glove(vocab_only=False):
    if vocab_only:
        print('Loading GloVe vocabulary...')
    else:
        print('Loading GloVe embeddings...')

    word_vocab = dict()
    embeddings_list = []
    with open(GLOVE_PATH, encoding='utf-8') as glove_file:
        for i, line in enumerate(glove_file):
            values = line.split()
            word = values[0]
            word_vocab[word] = i
            if not vocab_only:
                embedding = np.array(values[1:], dtype='float32')
                embeddings_list.append(embedding)

    # Add zero embedding for UNK
    word_vocab[UNK_word] = len(word_vocab)
    if not vocab_only:
        embeddings_list.append(np.zeros((EMBEDDING_DIM,)))

    embeddings = np.array(embeddings_list)

    return word_vocab, embeddings


def get_weighted_average_embeddings(sess, embedding, word_vocab, embeddings_dim, trigger_count):

    # print ("trigger_count:\t" + str(trigger_count))

    # trigger_count['trigger_idx']=word_vocab[trigger_count['trigger']]

    trigger_indices = []
    for x in trigger_count['trigger']:
        trigger_indices.append(word_vocab[x])

    # print ("trigger_indices:\t" + str(trigger_indices))

    # trigger_indices = trigger_count['trigger_idx']
    counts = trigger_count['count']

    dense_indices = np.stack((np.zeros(len(trigger_indices)), np.arange(len(trigger_indices))), axis=-1)

    idx = tf.SparseTensor(indices=dense_indices,
                          values=trigger_indices, dense_shape=[1, len(trigger_indices)])


    # weights = None
    weights = tf.SparseTensor(indices=dense_indices,
                              values=counts, dense_shape=[1, len(trigger_indices)])

    embed = tf.nn.embedding_lookup_sparse(embedding, idx, weights, combiner='sum')

    return sess.run(embed)


if __name__ == "__main__":
    date2trigger_counter = process_event_gigaword()
    date2vix_vals = process_vix_data()


    # load GloVe embeddings
    word_vocab, embeddings = load_glove()
    embedding = tf.Variable(embeddings)
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    triples = []
    for date, vix in date2vix_vals.items():
        if date in date2trigger_counter:
            triggers = []
            trigger_counter = date2trigger_counter[date]
            for trigger_count in trigger_counter.most_common(NUM_MOST_COMMON_TRIGGER_PER_TYPE):
                triggers.append((trigger_count[0], trigger_count[1]))
            for idx in range(0, NUM_MOST_COMMON_TRIGGER_PER_TYPE-len(triggers)):
                triggers.append((UNK_word, 0))
            triples.append((date, vix, triggers))
            # print ("triggers:\t" + str(triggers))

    # pickle.dump(triples, open("/nfs/raid88/u10/users/bmin/projects/events-socio-econ-indicators/gigaword-events/date_vix_triggers.p", "wb"))

    date_vix = []
    date_trigger_count = []
    for t in triples:
        date = t[0]
        vix = t[1]
        # date -> vix

        pair_date_vix = [date, vix]
        triples_date_trigger = []
        triggers = t[2]
        for p in triggers:
            trigger = p[0]
            if trigger not in word_vocab:
                trigger = UNK_word
            count = p[1]
            triples_date_trigger.append([date, trigger, count])

        if len(triples_date_trigger)>0:
            date_vix.append(pair_date_vix)
            date_trigger_count.extend(triples_date_trigger)
    # date_vix_dataset = pd.DataFrame({'date': date_vix[:][0], 'vix': date_vix[:][1]}).transpose()
    date_vix_dataset = pd.DataFrame(date_vix, columns=['date', 'vix'])

    # print (date_vix_dataset[0:10])
    #date_trigger_count_dataset = pd.DataFrame({'date': date_trigger_count[:][0], 'trigger': date_trigger_count[:][1], 'count': date_trigger_count[:][2]}).transpose()
    date_trigger_count_dataset = pd.DataFrame(date_trigger_count, columns=['date','trigger', 'count'])
    # print (date_trigger_count_dataset[0:10])

    with open("/nfs/raid88/u10/users/bmin/repositories/Hume/src/python/ecim/date_vix_triger_emb.csv", "w") as fp:
        for idx, row in date_vix_dataset.iterrows():
            date = row['date']
            vix = row['vix']
            # for date in date_vix_dataset['date']:
            # vix = date_vix_dataset.loc[date_vix_dataset['date']==date,['vix']].at[0, 'vix']

            trigger_count = date_trigger_count_dataset.loc[date_trigger_count_dataset['date']==date, ['trigger', 'count']]

            avg_embeddings = get_weighted_average_embeddings(sess, embedding, word_vocab, NUM_WORD_EMB_DIM, trigger_count)

            row = []
            row.append(date)
            row.append(vix)
            row.extend(avg_embeddings[0])

            row = [str(i) for i in row]

            # print (str(row))
            fp.write('\t'.join(row) + "\n")


