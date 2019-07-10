from os import listdir
from os.path import isfile, join
import xmltodict

class OntoNotesSenseInventory:

    def __init__(self):
        self.wn_sense_to_ontonotes_sense = dict()
        ontonotes_sense_inventory_dir = "/nfs/mercury-05/u34/shared/ontonotes-release-5.0_LDC2013T19/ontonotes-release-5.0/data/files/data/english/metadata/sense-inventories/"
        files = [f for f in listdir(ontonotes_sense_inventory_dir) if isfile(join(ontonotes_sense_inventory_dir, f))]

        print("loading sense inventory...")
        for file in files:
            path = ontonotes_sense_inventory_dir + file
            if file.endswith(".xml"):
                self.read_sense_mapping(path)
        print("sense inventory loaded.")

    def read_sense_mapping(self, xml_file):
        with open(xml_file) as fd:
            data = fd.read()

            result = xmltodict.parse(data)

            lemma_and_pos = result['inventory']['@lemma']
            lemma = lemma_and_pos[0:lemma_and_pos.rfind('-')]
            pos = lemma_and_pos[lemma_and_pos.rfind('-')+1:]

            if isinstance(result['inventory']['sense'], list):
                for sense in result['inventory']['sense']:
                    self.save_one_sense(lemma, pos, sense)
            else:
                sense = result['inventory']['sense']
                self.save_one_sense(lemma, pos, sense)
        fd.close

    def save_one_sense(self, lemma, pos, sense):
        onto_sense = sense['@group'] + "." + sense['@n']
        if '#text' in sense['mappings']['wn']:
            for wn_sense in sense['mappings']['wn']['#text'].split(","):
                key_wn_sense = lemma + "." + pos + "." + "0" + wn_sense
                key_onto_sense =  lemma + "-" + pos + "." + onto_sense
                self.wn_sense_to_ontonotes_sense[key_wn_sense] = key_onto_sense

    def hasOntoNotesSenseForWnSense(self, wn_sense):
        wn_sense = wn_sense[wn_sense.find("'")+1:-2] # hack to make Synset('deprive.v.02') look like deprive.v.02
        if wn_sense in self.wn_sense_to_ontonotes_sense:
            return True
        else:
            return False


if __name__ == '__main__':
    ontoNotesSenseInventory = OntoNotesSenseInventory()

    # test_file="/nfs/mercury-05/u34/shared/ontonotes-release-5.0_LDC2013T19/ontonotes-release-5.0/data/files/data/english/metadata/sense-inventories/attack-v.xml"
    # ontoNotesSenseInventory.parse_xml(test_file)

    # for wn_sense in ontoNotesSenseInventory.wn_sense_to_ontonotes_sense:
    #    print (wn_sense + "\t" + ontoNotesSenseInventory.wn_sense_to_ontonotes_sense[wn_sense])
