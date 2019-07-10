
import math
import argparse
import glob

aux_verbs = {'am','is','are','was','were','being','been','be','have','has','had','do','does','did','will','would','shall','should','may','might','must','can','could'}

stop_words = {'i','me','my','myself','we','us','our','ours','ourselves','you','your','yours','yourself','yourselves','he','him','his','himself','she','her','hers','herself','it','its','itself','they','them','their','theirs','themselves','what','which','who','whom','this','that','these','those','am','is','are','was','were','be','been','being','have','has','had','having','do','does','did','doing','would','should','could','ought','might','however','be','included','a','an','the','and','but','if','or','because','as','until','while','of','at','by','for','with','about','against','between','into','through','during','before','after','above','below','to','from','up','down','in','out','on','off','over','under','again','further','then','once','here','there','when','where','why','how','all','any','both','each','few','more','most','other','some','such','no','nor','not','only','own','same','so','than','too','very','one','every','least','less','many','now','ever','never','say','says','said','also','get','go','goes','just','made','make','put','see','seen','whether','like','well','back','even','still','way','take','since','another','however','new','old','high','long','one','two','three','four','five','six','seven','eight','nine','ten','first','second','third','fourth','fifth','sixth','seventh','eighth','nineth','tenth'}

class Vector(object):
    def __init__(self, filepath, weight_threshold=1):
        self.features = dict()

        keys = []
        weights = []
        norm = 0.0
        with open(filepath, 'r') as f:
            for line in f:
                tokens = line.strip().split()
                key = tokens[0]
                weight = float(tokens[1])
                if accept_word(key) and weight >= weight_threshold:
                    norm += weight * weight
                    keys.append(key)
                    weights.append(weight)

        self.norm = math.sqrt(norm)

        for i in range(len(keys)):
            self.features[keys[i]] = weights[i]/self.norm


def accept_word(w):
    if w.startswith("'") or w.startswith('http') or w.startswith('www') or w in aux_verbs or w in stop_words:
        return False
    else:
        return True


def cosine_similarity(v1, v2):
    """
    :type v1: Vector
    :type v2: Vector
    """

    if len(v1.features) < len(v2.features):
        small_feas = v1.features
        big_feas = v2.features
    else:
        small_feas = v2.features
        big_feas = v1.features

    prod = 0.0
    for key in small_feas.keys():
        if key in big_feas.keys():
            prod += small_feas[key] * big_feas[key]

    return prod / (v1.norm * v2.norm)


# python cosine_similarity.py --background_vector /nfs/raid87/u15/users/dakodes/issue-63/c-and-g-individual-and-background-counts/c-background-counts-all.txt --vector_files /nfs/raid87/u15/users/dakodes/issue-63/c-and-g-individual-and-background-counts/c-individual-counts --output_file c_prime.sim
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--background_vector')
    parser.add_argument('--vector_files')
    parser.add_argument('--output_file')
    args = parser.parse_args()


    background_vector = Vector(args.background_vector, 3)

    filepaths = []
    for filepath in glob.glob(args.vector_files+'/*'):
        filepaths.append(filepath)

    counter = 0
    sims = dict()
    for filepath in filepaths:
        v = Vector(filepath)
        sim = cosine_similarity(background_vector, v)
        sims[filepath] = sim
        #print('{} {}'.format(filepath, sim))
        counter += 1
        if (counter % 100)==0:
            print(counter)

    f = open(args.output_file, 'w')
    for key in sorted(sims, key=sims.get, reverse=True):
        f.write('{}\t{}\n'.format(key, sims[key]))
    f.close()


