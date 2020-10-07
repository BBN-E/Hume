import os,glob,json,collections,gzip


DocSentEntry = collections.namedtuple("DocSentEntry",['doc_id','sent_id','input_token_file_path','input_token_file_line_idx','number_of_bert_tokens'])

DocSentBatch = collections.namedtuple("DocSentBatch",["doc_id","sent_id","batch_id"])

def list_spliter_by_num_of_batches(my_list, num_of_batches):
    k, m = divmod(len(my_list), num_of_batches)
    return list(my_list[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(num_of_batches))

def main(input_sent_info_list,number_of_batches,batch_prefix,output_path,bert_job_list_path):

    # Step 1 Sorting sentences by number of bert tokens
    number_of_batches = int(number_of_batches)
    bert_token_length_array = list()
    relevant_input_token_file_paths = set()
    doc_id_set = set()
    with open(input_sent_info_list) as fp:
        for sent_info_path in fp:
            sent_info_path = sent_info_path.strip()
            input_token_file_path = os.path.realpath(os.path.join(sent_info_path,os.pardir,"input_token.info"))
            with gzip.open(sent_info_path,'rt') as fp2:
                for idx,line in enumerate(fp2):
                    line = line.strip()
                    en = json.loads(line)
                    doc_en = DocSentEntry(en['doc_id'],en['sent_id'],input_token_file_path,idx,en['number_of_bert_tokens'])
                    bert_token_length_array.append(doc_en)
                    relevant_input_token_file_paths.add(doc_en.input_token_file_path)
                    doc_id_set.add(doc_en.doc_id)
    bert_token_length_array = sorted(bert_token_length_array,key=lambda x:x.number_of_bert_tokens,reverse=True)

    batched_serialize_docid = list_spliter_by_num_of_batches(list(doc_id_set),number_of_batches)

    doc_id_to_batch_id = {}

    for batch_id,doc_ids in enumerate(batched_serialize_docid):
        for doc_id in doc_ids:
            doc_id_to_batch_id[doc_id] = batch_id


    # Step 2 Read in all input token file

    input_token_file_path_to_input_token_txt = dict()
    for input_token_file_path in relevant_input_token_file_paths:
        with gzip.open(input_token_file_path,'rt') as fp:
            input_token_file_path_to_input_token_txt[input_token_file_path] = fp.read().split("\n")

    # Step 3 Make batches

    batched_bert_token_length_array = list_spliter_by_num_of_batches(bert_token_length_array,number_of_batches)

    bert_job_list = list()

    for batch_id,batch_doc_sent_entries in enumerate(batched_bert_token_length_array):
        batch_output_dir = os.path.join(output_path,"{}{}".format(batch_prefix,batch_id))
        bert_job_list.append(batch_output_dir)
        os.makedirs(batch_output_dir,exist_ok=True)
        input_token_cnt_new = 0
        input_token_file_path_new = os.path.join(batch_output_dir,"input_token.info")
        input_token_file_line_idx_new = os.path.join(batch_output_dir,"sent_info.info")
        with gzip.open(input_token_file_line_idx_new,'wt') as sent_info_wfp:
            with gzip.open(input_token_file_path_new,'wt') as input_token_wfp:
                for batch_doc_sent_entry in batch_doc_sent_entries:
                    input_token_text = input_token_file_path_to_input_token_txt[batch_doc_sent_entry.input_token_file_path][batch_doc_sent_entry.input_token_file_line_idx]
                    new_doc_sent_en = DocSentBatch(batch_doc_sent_entry.doc_id,batch_doc_sent_entry.sent_id,doc_id_to_batch_id[batch_doc_sent_entry.doc_id])
                    input_token_wfp.write("{}\n".format(input_token_text))
                    input_token_cnt_new += 1
                    sent_info_wfp.write("{}\n".format(json.dumps(dict(new_doc_sent_en._asdict()))))

    with open(bert_job_list_path,'w') as wfp:
        for i in bert_job_list:
            wfp.write("{}\n".format(i))



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_sent_info_list")
    parser.add_argument("--number_of_batches")
    parser.add_argument("--batch_prefix")
    parser.add_argument("--output_path")
    parser.add_argument("--bert_job_list_path")
    args = parser.parse_args()
    main(args.input_sent_info_list,args.number_of_batches,args.batch_prefix,args.output_path,args.bert_job_list_path)
