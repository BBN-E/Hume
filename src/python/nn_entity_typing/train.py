# -*- coding: utf-8 -*-
import argparse
from src.model.nn_model import Model
from src.batcher import Batcher
from src.hook import acc_hook, save_predictions
import os
from sklearn.externals import joblib
import pickle
parser = argparse.ArgumentParser()
parser.add_argument("dataset",help="dataset to train model")
parser.add_argument("encoder",help="context encoder to use in model",choices=["averaging","lstm","attentive"])
parser.add_argument("--model_output_dir",dest="model_output_dir",help="directory to save model files to; default value is present working directory")
parser.add_argument('--feature', dest='feature', action='store_true')
parser.add_argument('--no-feature', dest='feature', action='store_false')
parser.set_defaults(model_output_dir=os.getcwd())
parser.set_defaults(feature=False)
parser.add_argument('--hier', dest='hier', action='store_true')
parser.add_argument('--no-hier', dest='hier', action='store_false')
parser.set_defaults(hier=False)
args = parser.parse_args()


print "Creating the model"
d = args.dataset
target_dim = 0
with open("resource/"+d+"/label2id_figer.txt",'r') as fp:
    for i in fp:
        target_dim += 1

model = Model(type="figer",encoder=args.encoder,hier=args.hier,feature=args.feature,target_dim=target_dim)


print "Loading the dictionaries"
# d = "Wiki" if args.dataset == "figer" else "OntoNotes"

dicts = joblib.load("data/"+d+"/dicts_figer.pkl")

print "Loading the datasets"
train_dataset = joblib.load("data/"+d+"/train_figer.pkl")
dev_dataset = joblib.load("data/"+d+"/dev_figer.pkl")
test_dataset = joblib.load("data/"+d+"/test_figer.pkl")

print 
print "train_size:", train_dataset["data"].shape[0]
print "dev_size: ", dev_dataset["data"].shape[0]
print "test_size: ", test_dataset["data"].shape[0]

print "Creating batchers"
# batch_size : 1000, context_length : 10
train_batcher = Batcher(train_dataset["storage"],train_dataset["data"],1000,10,dicts["id2vec"])
dev_batcher = Batcher(dev_dataset["storage"],dev_dataset["data"],dev_dataset["data"].shape[0],10,dicts["id2vec"])
test_batcher = Batcher(test_dataset["storage"],test_dataset["data"],test_dataset["data"].shape[0],10,dicts["id2vec"])

# step_par_epoch = 2000 if args.dataset == "figer" else 150
# Bonan: 31 is hard-coded number (number of batches): 31*1000 (batch size) should be less than the total number of training instances
step_par_epoch = int(train_dataset["data"].shape[0] / 1000)

print "start trainning"
for epoch in range(5):
    train_batcher.shuffle()
    print "epoch",epoch
    for i in range(step_par_epoch):
        print "step",i
        context_data, mention_representation_data, target_data, feature_data = train_batcher.next()
        model.train(context_data, mention_representation_data, target_data, feature_data)
        
    print "------dev--------"
    context_data, mention_representation_data, target_data, feature_data = dev_batcher.next()
    scores = model.predict(context_data, mention_representation_data,feature_data)
    acc_hook(scores, target_data)

print "Training completed.  Below are the final test scores: "
print "Saving model"
model.save(os.path.join(args.model_output_dir,"NFGEC_tf_session"),"data/"+d+"/dicts_figer.pkl")
# using a hard-coded prefix 'NFGEC_tf_session'; the same will be used by decode.py

print "-----test--------"
context_data, mention_representation_data, target_data, feature_data = test_batcher.next()
scores = model.predict(context_data, mention_representation_data, feature_data)
acc_hook(scores, target_data)
fname = args.dataset + "_" + args.encoder + "_" + str(args.feature) + "_" + str(args.hier) + ".txt"
save_predictions(scores, target_data, dicts["id2label"],fname)

print "Cheers!"
