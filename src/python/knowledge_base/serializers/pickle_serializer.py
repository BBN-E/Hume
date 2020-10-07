from elements.kb_mention import KBMention
from elements.kb_value_mention import KBValueMention, KBTimeValueMention, KBMoneyValueMention
import pickle
import os

class KBPickleSerializer:

    def __init__(self):
        pass

    def serialize(self, kb, output_pickle_file):
        print("KBPickleSerializer SERIALIZE")
        dir_path = os.path.dirname(os.path.realpath(output_pickle_file))
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        with open(output_pickle_file, "wb") as pickle_file:
            pickle.dump(kb, pickle_file)

