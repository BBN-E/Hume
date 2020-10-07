import os,ast,json,logging,multiprocessing,re,datetime
logger = logging.getLogger(__name__)

import serifxml3


# def txt_to_serif_doc(s,docid):
#     logger.info("Creating a SERIF XML document")
#     new_doc = serifxml3.Document.construct(docid)
#     new_doc.language = "English"
#     new_doc.construct_original_text(s, 0, len(s) - 1)
#     new_doc.construct_regions(0, len(s) - 1)
#     new_doc.construct_segments()
#     new_doc.construct_metadata(0, len(s) - 1, "RegionSpan", "TEXT")
#     return new_doc
#
# def my_tokenizer(serif_doc,eer_json_en):
#     assert len(serif_doc.sentences) == 1
#     sentence = serif_doc.sentences[0]
#     token_sequence = sentence.add_new_token_sequence(0.7)
#     tokens = eer_json_en['token']
#     cursor = 0
#     for i in tokens:
#         start_char_off = sentence.text.find(i,cursor)
#         assert start_char_off != -1
#         end_char_off = start_char_off + len(i) - 1
#         token_sequence.add_new_token(start_char_off,end_char_off,i)
#         cursor = end_char_off + 1

def read_metadata_file(metadata_file):
    docid_to_document_properties = dict()
    m = open(metadata_file, 'r')
    for line in m:
        pieces = line.strip().split("\t")
        document_properties = dict()
        docid = pieces[0]
        document_properties["docid"] = docid
        document_properties["doc_type"] = pieces[4].strip()
        document_properties["source"] = re.sub("^\./", "", re.sub("\n", " ", pieces[1]))
        document_properties["uuid"] = pieces[6]
        document_properties["filename"] = re.sub("\n", " ", pieces[5])
        document_properties["credibility"] = float(pieces[3])
        date_created_str = pieces[2]
        if date_created_str != "UNKNOWN":
            document_properties["date_created"] = datetime.datetime.strptime(date_created_str, "%Y%m%d").strftime("%Y-%m-%d")
        else:
            document_properties["date_created"] = "UNKNOWN"
        document_properties["offset"] = 0
        if len(pieces) > 7:
            document_properties["offset"] = int(pieces[7])
        document_properties["author"] = "UNKNOWN"
        if len(pieces) > 8:
            document_properties["author"] = pieces[8]
        document_properties["online_source"] = "UNKNOWN"
        if len(pieces) > 9:
            document_properties["online_source"] = pieces[9]
        if len(pieces) > 10:
            print("Too many pieces")
            sys.exit(1)
        docid_to_document_properties[docid] = document_properties
    return docid_to_document_properties

def create_doc_id_to_p(filelist_path,suffix=".xml"):
    doc_id_to_p = dict()
    s = set()
    with open(filelist_path) as fp:
        for i in fp:
            i = i.strip()
            docid = os.path.basename(i)
            docid = docid[:-len(suffix)]
            if docid not in doc_id_to_p:
                doc_id_to_p[docid] = i
            else:
                old_e = int(doc_id_to_p[docid].split("/")[-2].replace("E",""))
                current_e = int(i.split("/")[-2].replace("E",""))
                if current_e > old_e:
                    s.add((doc_id_to_p[docid],i))
                    doc_id_to_p[docid] = i
                else:
                    s.add((i,doc_id_to_p[docid]))
    for i in s:
        logger.error("Duplicated detected {} {}".format(i[0],i[1]))
    return doc_id_to_p

def find_lowest_common_ancestor(syn_node_1, syn_node_2):
    # https://www.hrwhisper.me/algorithm-lowest-common-ancestor-of-a-binary-tree
    assert isinstance(syn_node_1, serifxml3.SynNode)
    assert isinstance(syn_node_2, serifxml3.SynNode)
    visited = set()
    while syn_node_1 is not None and syn_node_2 is not None:
        if syn_node_1 is not None:
            if syn_node_1 in visited:
                return syn_node_1
            visited.add(syn_node_1)
            syn_node_1 = syn_node_1.parent
        if syn_node_2 is not None:
            if syn_node_2 in visited:
                return syn_node_2
            visited.add(syn_node_2)
            syn_node_2 = syn_node_2.parent
    return None

def get_or_create_em(serif_doc,offsets_to_em,start_char,end_char,offset,en,h_or_t):
    orig_start = start_char
    orig_end = end_char
    start_char = start_char - offset
    end_char = end_char - offset
    if (start_char,end_char) in offsets_to_em:
        return offsets_to_em[(start_char,end_char)]
    else:
        for sentence in serif_doc.sentences:
            if sentence.start_char <= start_char and sentence.end_char >= end_char:
                token_start_edt_to_token = {token.start_char: token for token in sentence.token_sequence}
                token_end_edt_to_token = {token.end_char: token for token in sentence.token_sequence}
                event_mention_set = sentence.sentence_theory.event_mention_set
                if start_char not in token_start_edt_to_token:
                    start_char = start_char + 1
                if start_char not in token_start_edt_to_token:
                    start_char = start_char - 2
                if end_char not in token_end_edt_to_token:
                    end_char = end_char + 1
                if end_char not in token_end_edt_to_token:
                    end_char = end_char - 2
                if start_char not in token_start_edt_to_token or end_char not in token_end_edt_to_token:
                    for token in sentence.token_sequence:
                        if token.text.lower() == en[h_or_t]['name'].split(" ")[0]:
                            start_char = token.start_char
                        if token.text.lower() == en[h_or_t]['name'].split(" ")[-1]:
                            end_char = token.end_char
                if start_char not in token_start_edt_to_token or end_char not in token_end_edt_to_token:
                    logger.critical("{} skipping {} {} {}".format(serif_doc.docid,orig_start,orig_end," ".join("{}-{} {} ".format(token.start_char,token.end_char,token.text) for token in sentence.token_sequence)))
                    return None
                start_token = token_start_edt_to_token[start_char]
                end_token = token_end_edt_to_token[end_char]
                event_anchor_synnode = find_lowest_common_ancestor(start_token.syn_node, end_token.syn_node)
                event_mention = event_mention_set.add_new_event_mention(
                    "LDC_EVENT", event_anchor_synnode, 1.0)
                offsets_to_em[(start_char,end_char)] = event_mention
                return event_mention

def single_document_handler(serif_path,entries,output_path,offset):
    hit = 0
    miss = 0
    try:
        exist_eerms = dict()
        offsets_to_em = dict()
        serif_doc = serifxml3.Document(serif_path)
        for sentence in serif_doc.sentences:
            for event_mention in sentence.sentence_theory.event_mention_set:
                start_off = event_mention.anchor_node.start_char
                end_off = event_mention.anchor_node.end_char
                offsets_to_em[(start_off,end_off)] = event_mention
        # serif_eerm_set = serif_doc.event_event_relation_mention_set
        # if serif_eerm_set is None:
        #     serif_eerm_set = serif_doc.add_new_event_event_relation_mention_set()
        serif_eerm_set = serif_doc.add_new_event_event_relation_mention_set()
        for serif_eerm in serif_eerm_set:
            serif_em_arg1 = None
            serif_em_arg2 = None
            relation_type = serif_eerm.relation_type
            confidence = serif_eerm.confidence
            for arg in serif_eerm.event_mention_relation_arguments:
                if arg.role == "arg1":
                    serif_em_arg1 = arg.event_mention
                if arg.role == "arg2":
                    serif_em_arg2 = arg.event_mention
            if serif_em_arg1 is not None and serif_em_arg2 is not None:
                exist_eerms[(serif_em_arg1,relation_type,serif_em_arg2)] = serif_eerm

        for en in entries:
            left_em_start,left_em_end = en['arg1_span_list'][0]
            right_em_start,right_em_end = en['arg2_span_list'][0]

            left_em = get_or_create_em(serif_doc,offsets_to_em,left_em_start,left_em_end,offset,en,'h')
            right_em = get_or_create_em(serif_doc,offsets_to_em,right_em_start,right_em_end,offset,en,'t')
            if left_em is None or right_em is None:
                logger.critical("Skipping {}".format(json.dumps(en)))
                miss += 1
                continue
            relation_type = en['semantic_class']
            if (left_em,relation_type,right_em) in exist_eerms:
                exist_eerms[(left_em,relation_type,right_em)].model = "LDC"
                exist_eerms[(left_em, relation_type, right_em)].confidence = 1.0
            else:
                eerm = serif_eerm_set.add_new_event_event_relation_mention(
                    relation_type, 1.0, "LDC")
                eerm.add_new_event_mention_argument("arg1", left_em)
                eerm.add_new_event_mention_argument("arg2", right_em)
                exist_eerms[(left_em,relation_type,right_em)] = eerm
            hit += 1
        serif_doc.save(os.path.join(output_path,"{}.xml".format(serif_doc.docid)))
    except Exception as e:
        import traceback
        logger.critical("{} {}".format(serif_doc.docid,traceback.format_exc()))
        miss += 1
    finally:
        return hit,miss


def pipeline():
    eer_json_ens = list()
    with open("/home/hqiu/ld100/crdg/output/mention_pool.json") as fp:
        for i in fp:
            i = i.strip()
            eer_json_ens.append(json.loads(i))

    doc_id_to_p = create_doc_id_to_p("/home/hqiu/ld100/crdg/output/serifxml.list")
    doc_id_to_metadata_en = dict()
    for epoch in ["E48","E61","E70","E82","E83"]:
        metadata_path = "/home/hqiu/ld100/crdg/sgm_lists/{}/metadata.txt".format(epoch)
        d = read_metadata_file(metadata_path)
        doc_id_to_metadata_en.update(d.items())
    doc_id_to_dart_p = create_doc_id_to_p("/nfs/raid88/u10/users/hqiu/serifxml_lists/wm_dart_101519.vexpt1.list")
    doc_id_to_en = dict()
    for i in eer_json_ens:
        doc_id_to_en.setdefault(i['docid'],list()).append(i)
    output_path = "/home/hqiu/tmp/eerm_serifs"
    manager = multiprocessing.Manager()
    hit = 0
    miss = 0
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        for doc_id in doc_id_to_p.keys():
            p = doc_id_to_p[doc_id]
            en = doc_id_to_en.get(doc_id,list())
            job = pool.apply_async(single_document_handler,args=(p,en,output_path,doc_id_to_metadata_en[doc_id]['offset'],))
            workers.append(job)
        for doc_id in doc_id_to_dart_p.keys():
            p = doc_id_to_dart_p[doc_id]
            en = doc_id_to_en.get(doc_id,list())
            job = pool.apply_async(single_document_handler,args=(p,en,output_path,0,))
            workers.append(job)
        for idx,i in enumerate(workers):
            i.wait()
            hit_a,miss_a = i.get()
            hit += hit_a
            miss += miss_a
    logger.critical("Total: {} Hit: {} Miss: {}".format(len(eer_json_ens),hit,miss))

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    pipeline()