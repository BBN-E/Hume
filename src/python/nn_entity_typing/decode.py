# -*- coding: utf-8 -*-
import argparse
from sklearn.externals import joblib
from src.model.nn_model import Model
from src.batcher import Batcher
from src.hook import acc_hook, save_predictions
import sys
import os


parser = argparse.ArgumentParser()
parser.add_argument("model_files_dir",help="path to directory with model files (and model init params file)")
parser.add_argument("dictionary",help="path to pkl file containing various dictionaries (e.g. id2vec) created during training")
parser.add_argument("dataset",help="path to decoding dataset pkl file")
parser.add_argument("output",help="path to predictions file")
args = parser.parse_args()

print "Loading the model..."
model = Model.load(os.path.join(args.model_files_dir,"NFGEC_tf_session"))

print "Loading dictionaries..."
dicts = joblib.load(args.dictionary)

print "Loading the decoding dataset..."
decode_dataset = joblib.load(args.dataset)

decode_size = decode_dataset["data"].shape[0]

print "decode_size: ", decode_size

# if decode_size is 0 (i.e. the decode_dataset is empty), the serif-instances file must have been empty
# this can happen if the serif name-list adder did not find any names to add as mentions (e.g. if you are using a very short text)
# in such a case, exit with success
if decode_size == 0:
    print "Exiting decoding since decode dataset is empty!"
    # save an empty output file; this will avoid other steps in the CauseEX pipeline from failing
    with(open(args.output,"w")) as fp:
        pass
    sys.exit(0)

if decode_dataset["data"].shape[0]==0:
    print "Dataset is empty. Exit"
    sys.exit()

print "Creating batcher..."
test_batcher = Batcher(decode_dataset["storage"],decode_dataset["data"],decode_dataset["data"].shape[0],10,dicts["id2vec"])

print "Getting bacther.next..."
context_data, mention_representation_data, target_data, feature_data = test_batcher.next()

print "Running decoding..."
scores = model.predict(context_data, mention_representation_data, feature_data)
acc_hook(scores, target_data)
save_predictions(scores, target_data, dicts["id2label"],args.output)

print "Finished decoding! Predicted labels written to: "+args.output
