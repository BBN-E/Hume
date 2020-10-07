


def cat(input_list,output_file):
    res = ""
    with open(input_list) as fp:
        for i in fp:
            i = i.strip()
            with open(i) as fp2:
                res += fp2.read()
    with open(output_file,'w') as wfp:
        wfp.write(res)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_segment_list', required=True)
    parser.add_argument('--output_file', required=True)
    args = parser.parse_args()
    cat(args.input_segment_list,args.output_file)