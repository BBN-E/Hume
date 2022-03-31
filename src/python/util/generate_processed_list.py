import os,json

def main():
    input_dir = "/home/hqiu/tmp/dart.071721/"
    output_file = "/home/hqiu/tmp/processed.log"
    with open(output_file,'w') as wfp:
        for file in os.listdir(input_dir):
            msg_id = os.path.basename(file)[:-len(".txt")]
            # with open(os.path.join(input_dir,file)) as fp:
            #     j = json.load(fp)
            #     uuid = j['document_id']
            wfp.write("{}\t{}\n".format(msg_id,msg_id))



if __name__ == "__main__":
    main()