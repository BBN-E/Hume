from pprint import pprint
import nltk
from nltk.corpus import framenet as fn
from nltk.stem import WordNetLemmatizer

nltk.data.path.append('/nfs/mercury-04/u42/bmin/applications/nltk_data/')

# https://arxiv.org/pdf/1703.07438.pdf
# http://naacl.org/naacl-hlt-2015/tutorial-framenet-data/FrameNetAPI.pdf

class TriggerClassifier:

    def __init__(self, use_positive=True):
        self.use_positive = use_positive

        print('Loading annotated triggers...')

        if self.use_positive:
            list_triggers = []
            file_in = '/nfs/ld100/u10/bmin/repositories/CauseEx/experiments/generic_trigger_finding_and_filtering/causeex-month3.triggers.txt.freq.annotated_top1600'
            with open(file_in) as fd:
                for line in fd.readlines():
                    if line.startswith("#") or line.startswith(" ") or line.startswith("\t"):
                        continue

                    line = line.strip()
                    items = line.split(" ")

                    label = items[0].strip()
                    word = items[len(items)-1].strip().lower()

                    if label == "1":
                        list_triggers.append(word)
                        # print ("word: " + word)
            self.list_good_triggers = set(list_triggers)
        else: # use negative list
            print("init use_positive=False")
            list_not_triggers = []
            file_in = '/nfs/ld100/u10/bmin/repositories/CauseEx/expts/causeex_m3_and_wm_starter.v1/list_bad_triggers'
            with open(file_in) as fd:
                for line in fd.readlines():
                    if line.startswith("#") or line.startswith(" ") or line.startswith("\t"):
                        continue

                    line = line.strip()
                    items = line.split(" ")

                    label = items[0].strip()
                    word = items[len(items) - 1].strip().lower()

                    if label == "0":
                        list_not_triggers.append(word)
                        # print ("word: " + word)
            self.list_bad_triggers = set(list_not_triggers)

    def isValidEventTrigger(self, word):
        word = word.strip().lower()

        if self.use_positive:
            if word in self.list_good_triggers:
                return True
            else:
                return False
        else:
            if word in self.list_bad_triggers:
                return False
            else:
                return True

if __name__ == '__main__':
    triggerClassifier = TriggerClassifier()

    word = "attack"
    print(word + "\t" + str(triggerClassifier.isValidEventTrigger(word)))

    word = "book"
    print(word + "\t" + str(triggerClassifier.isValidEventTrigger(word)))




# print(fn.lu('attack').name + fn.lu('attack').POS)


#for lu in fn.lus():
#    print("== word: " + lu.name + "\t" + lu.POS) # + "\t" + lu.definition + "\t" + lu.frame.name + "\t" + lu.lexemes[0].name)
