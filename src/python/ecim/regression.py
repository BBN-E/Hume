from __future__ import absolute_import, division, print_function, unicode_literals

import pathlib

#import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# import seaborn as sns

import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers

import pickle
import codecs
import os

print(tf.__version__)

pickle_triples = open("/nfs/raid88/u10/users/bmin/projects/events-socio-econ-indicators/gigaword-events/date_vix_triggers.p", "rb")
triples = pickle.load(pickle_triples)



load_data()

#import tensorflow_docs as tfdocs
#import tensorflow_docs.plots
#import tensorflow_docs.modeling

column_names = ['MPG','Cylinders','Displacement','Horsepower','Weight','Acceleration', 'Model Year', 'Origin']
dataset_path = "./auto-mpg.data"
raw_dataset = pd.read_csv(dataset_path, names=column_names, na_values = "?", comment='\t', sep=" ", skipinitialspace=True)

dataset = raw_dataset.copy()
# dataset.tail()

dataset = dataset.dropna()

dataset['Origin'] = dataset['Origin'].map(lambda x: {1: 'USA', 2: 'Europe', 3: 'Japan'}.get(x))

dataset = pd.get_dummies(dataset, prefix='', prefix_sep='')
# dataset.tail()

train_dataset = dataset.sample(frac=0.8,random_state=0)
test_dataset = dataset.drop(train_dataset.index)

# sns.pairplot(train_dataset[["MPG", "Cylinders", "Displacement", "Weight"]], diag_kind="kde")

train_stats = train_dataset.describe()
train_stats.pop("MPG")
train_stats = train_stats.transpose()
# train_stats

train_labels = train_dataset.pop('MPG')
test_labels = test_dataset.pop('MPG')

def norm(x):
  return (x - train_stats['mean']) / train_stats['std']
normed_train_data = norm(train_dataset)
normed_test_data = norm(test_dataset)


def build_model():
  model = keras.Sequential([
    layers.Dense(64, activation='relu', input_shape=[len(train_dataset.keys())]),
    layers.Dense(64, activation='relu'),
    layers.Dense(1)
  ])

  optimizer = tf.keras.optimizers.RMSprop(0.001)

  model.compile(loss='mse',
                optimizer=optimizer,
                metrics=['mae', 'mse'])
  return model

model = build_model()

model.summary()

example_batch = normed_train_data[:10]
example_result = model.predict(example_batch)
# example_result

EPOCHS = 1000

history = model.fit(
  normed_train_data, train_labels,
  epochs=EPOCHS, validation_split = 0.2, verbose=0,
  callbacks=[])


hist = pd.DataFrame(history.history)
hist['epoch'] = history.epoch
# hist.tail()

# plotter = tfdocs.plots.HistoryPlotter(smoothing_std=2)

# plotter.plot({'Basic': history}, metric = "mae")
# plt.ylim([0, 10])
# plt.ylabel('MAE [MPG]')

# Text(0, 0.5, 'MAE [MPG]')

model = build_model()

# The patience parameter is the amount of epochs to check for improvement
early_stop = keras.callbacks.EarlyStopping(monitor='val_loss', patience=10)

early_history = model.fit(normed_train_data, train_labels,
                    epochs=EPOCHS, validation_split = 0.2, verbose=0,
                    callbacks=[early_stop])

# plotter.plot({'Early Stopping': early_history}, metric = "mae")
# plt.ylim([0, 10])
# plt.ylabel('MAE [MPG]')
# Text(0, 0.5, 'MAE [MPG]')

loss, mae, mse = model.evaluate(normed_test_data, test_labels, verbose=2)

print("Testing set Mean Abs Error: {:5.2f} MPG".format(mae))

test_predictions = model.predict(normed_test_data).flatten()

# a = plt.axes(aspect='equal')
# plt.scatter(test_labels, test_predictions)
# plt.xlabel('True Values [MPG]')
# plt.ylabel('Predictions [MPG]')
# lims = [0, 50]
# plt.xlim(lims)
#plt.ylim(lims)
# _ = plt.plot(lims, lims)


error = test_predictions - test_labels
print (error)
# plt.hist(error, bins = 25)
# plt.xlabel("Prediction Error [MPG]")
# _ = plt.ylabel("Count")
