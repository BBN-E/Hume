from pprint import pprint
import nltk
from nltk.corpus import framenet as fn
from nltk.stem import WordNetLemmatizer

nltk.data.path.append('/nfs/mercury-04/u42/bmin/applications/nltk_data/')

# https://arxiv.org/pdf/1703.07438.pdf
# http://naacl.org/naacl-hlt-2015/tutorial-framenet-data/FrameNetAPI.pdf

class FrameNetUtil:

    def __init__(self):
        print('Initializing FrameNet.')
        self.lus = set()
        self.wordnet_lemmatizer = WordNetLemmatizer()

        file_lus = '/nfs/mercury-05/u34/shared/FrameNet/fndata-1.7.lexical_units_and_pos'

        with open(file_lus) as fd:
            for line in fd.readlines():
                line = line.strip()
                items = line.split("\t")
                if items[1] == "N" or items[1] == "V":
                    word = items[0][0:items[0].rfind(".")]
                    self.lus.add(word)

    def getEventTriggersWithPosAndIndex(self, tokens):
        token_and_pos_and_isTriggers = []
        token_and_poss = nltk.pos_tag(tokens)
        for token_and_pos in token_and_poss:
            token = token_and_pos[0]
            pos = token_and_pos[1][0:1].lower()

            isTrigger = False
            if pos == 'v' or pos == 'n':
                isTrigger = self.isValidEventTrigger(token, pos)

            token_and_pos_and_isTrigger = token_and_pos + (isTrigger,)
            token_and_pos_and_isTriggers.append(token_and_pos_and_isTrigger)

        return token_and_pos_and_isTriggers

    def isValidEventTrigger(self, word, pos='n'):
        word = self.wordnet_lemmatizer.lemmatize(word, pos)

        if word in self.lus:
            return True
        else:
            return False

if __name__ == '__main__':
    fnu = FrameNetUtil()
    sent = "Jonathan killed a dog";

    print(str(fnu.getEventTriggersWithPosAndIndex(sent.split(" "))))





# print(fn.lu('attack').name + fn.lu('attack').POS)


#for lu in fn.lus():
#    print("== word: " + lu.name + "\t" + lu.POS) # + "\t" + lu.definition + "\t" + lu.frame.name + "\t" + lu.lexemes[0].name)
