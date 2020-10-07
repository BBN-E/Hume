import pickle
from collections import Counter

def main(input_list, output_dir):
	with open(input_list) as f:
		count_list = f.readlines()
	count_list = [x.strip() for x in count_list] 

	final_dict = dict()
	for count_path in count_list:
		with open(count_path, 'rb') as handle:
			word_pair_to_count = pickle.load(handle)
			final_dict = dict(Counter(final_dict)+Counter(word_pair_to_count))

	final_result = output_dir + '/aggregate_counts.pkl'
	with open(final_result, 'wb') as handle:
		pickle.dump(final_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_list")
    parser.add_argument("--output_dir")
    args = parser.parse_args()
    main(args.input_list,args.output_dir)
