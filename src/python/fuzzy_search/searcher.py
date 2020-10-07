import abc
import os,sys
import typing
import serifxml3
import json

current_root = os.path.realpath(os.path.join(__file__,os.pardir,os.pardir))
sys.path.append(os.path.join(current_root))

from fuzzy_search.prepare_corpus import my_escaper,get_canonical_name,get_entity_to_actor_entity_cache

class Searcher(abc.ABC):
    @abc.abstractmethod
    def query(self,event_string:str,entity_string_or:str,entity_string_and:str) -> typing.List[str]:
        pass


def get_longest_string(lst):
    longest_string = None
    l = None
    for e in lst:
        if l is None or len(e) > l:
            longest_string = e
            l = len(e)
    return longest_string



def attach_extra_event_arguments(doc_id,doc_path,segment_ids):
    serif_doc = serifxml3.Document(doc_path)


    serif_entity_to_serif_actor_entity = get_entity_to_actor_entity_cache(serif_doc)

    mention_to_entity = dict()
    entity_to_canonical_name = dict()

    for serif_entity in serif_doc.entity_set:
        serif_actor_entity = serif_entity_to_serif_actor_entity.get(serif_entity)
        canonical_name = get_canonical_name(serif_entity, serif_actor_entity)
        entity_to_canonical_name[serif_entity] = canonical_name
        for serif_mention in serif_entity.mentions:
            mention_to_entity[serif_mention] = serif_entity


    segment_id_to_canonical_names = dict()
    segment_id_to_anchor_strings = dict()
    segment_id_to_canonical_names_in_sentence = dict()
    segment_id_to_sentence_string = dict()
    sent_start_to_mention_to_segment_id = dict()
    for segment_id in segment_ids:
        doc_id,sent_start_char,anchor_start_off = segment_id.split("-")
        sent_start_char = int(sent_start_char)
        anchor_start_off = int(anchor_start_off)
        sent_start_to_mention_to_segment_id.setdefault(sent_start_char,dict())[anchor_start_off] = segment_id
    for sent_idx,sentence in enumerate(serif_doc.sentences):
        for sentence_theory in sentence.sentence_theories:
            if len(sentence_theory.token_sequence) < 1:
                continue
            sent_start_char = int(sentence.start_char)
            canonical_names_in_sentence = set()
            if sent_start_char in sent_start_to_mention_to_segment_id.keys():
                for serif_mention in sentence_theory.mention_set:
                    canonical_name = entity_to_canonical_name.get(mention_to_entity.get(serif_mention, None),None)
                    if canonical_name is not None:
                        canonical_names_in_sentence.add(canonical_name)
                for serif_em in sentence_theory.event_mention_set:
                    anchor_start_off = int(serif_em.anchor_node.start_char)
                    if anchor_start_off in sent_start_to_mention_to_segment_id[sent_start_char].keys():
                        event_text = list()
                        event_type_text = set()


                        for anchor in serif_em.anchors:
                            anchor_node = anchor.anchor_node
                            event_text.extend([my_escaper(i).lower() for i in anchor_node.text.split(" ")])
                        # for event_type in serif_em.event_types:
                        #     event_type_text.add("EVENT-{}".format(event_type.event_type))
                        event_mention_str = "{}".format(" ".join(event_text))
                        canonical_names = set()
                        for argument in serif_em.arguments:
                            if argument.mention != None:
                                if entity_to_canonical_name.get(mention_to_entity.get(argument.mention, None),None) is not None:
                                    canonical_names.add(entity_to_canonical_name.get(mention_to_entity.get(argument.mention, None),None))
                        segment_id_to_canonical_names[sent_start_to_mention_to_segment_id[sent_start_char][anchor_start_off]]  = canonical_names
                        segment_id_to_anchor_strings[sent_start_to_mention_to_segment_id[sent_start_char][anchor_start_off]]  = event_mention_str
                        segment_id_to_canonical_names_in_sentence[sent_start_to_mention_to_segment_id[sent_start_char][anchor_start_off]] = canonical_names_in_sentence
                        segment_id_to_sentence_string[sent_start_to_mention_to_segment_id[sent_start_char][anchor_start_off]] = " ".join(token.text for token in sentence_theory.token_sequence)
    return segment_id_to_canonical_names,segment_id_to_anchor_strings,segment_id_to_canonical_names_in_sentence,segment_id_to_sentence_string

def single_document_worker(doc_id,doc_path,segments,entity_string_and,entity_strings_or):
    ret = list()
    segment_id_to_canonical_names,segment_id_to_anchor_strings,segment_id_to_canonical_names_in_sentence,segment_id_to_sentence_string = attach_extra_event_arguments(doc_id,doc_path,segments)
    for segment in segments:
        if len(entity_string_and) < 1 and len(entity_strings_or) < 1:
            ret.append([segment_id_to_anchor_strings[segment],segment_id_to_sentence_string[segment]])
        else:
            all_entity_string_in_canonical_name_set = True
            for entity_string in entity_string_and:
                if entity_string not in segment_id_to_canonical_names.get(segment,set()):
                    all_entity_string_in_canonical_name_set = False
                    break
            at_least_one_or_string_appears = True if len(entity_strings_or)<1 else False
            for entity_string in entity_strings_or:
                if entity_string in segment_id_to_canonical_names.get(segment,set()):
                    at_least_one_or_string_appears = True
                    break
            if all_entity_string_in_canonical_name_set is True and at_least_one_or_string_appears is True:
                ret.append([segment_id_to_anchor_strings[segment],segment_id_to_sentence_string[segment]])
            # else:
            #     all_entity_string_in_canonical_name_set = True
            #     for entity_string in entity_string_and:
            #         if entity_string not in segment_id_to_canonical_names_in_sentence.get(segment,set()):
            #             all_entity_string_in_canonical_name_set = False
            #             break
            #     at_least_one_or_string_appears = True if len(entity_strings_or)<1 else False
            #     for entity_string in entity_strings_or:
            #         if entity_string in segment_id_to_canonical_names_in_sentence.get(segment,set()):
            #             at_least_one_or_string_appears = True
            #             break
            #     if all_entity_string_in_canonical_name_set is True and at_least_one_or_string_appears is True:
            #         ret.append([segment_id_to_anchor_strings[segment],segment_id_to_sentence_string[segment]])
    return ret


class CLIRSearcher(Searcher):
    def __init__(self,serifxml_list,shrinked_down_query_file,input_json_path):
        self.doc_id_to_doc_list = dict()
        self.query_to_result = dict()
        with open(serifxml_list) as fp:
            for i in fp:
                i = i.strip()
                docid = os.path.basename(i)
                docid = docid.split(".xml")[0]
                self.doc_id_to_doc_list[docid] = i
        self.event_string_to_query_id_map = dict()
        with open(shrinked_down_query_file) as fp:
            for i in fp:
                i = i.strip()
                if i.startswith("############"):
                    continue
                query_id, segment_id, relevance_score = i.split("\t")
                query_id_cleaned = "_".join(query_id.split("_")[:-1])
                self.query_to_result.setdefault(query_id_cleaned, dict())[segment_id] = relevance_score
        self.event_string_to_query_id_map = dict()
        with open(input_json_path) as fp:
            j = json.load(fp)

        for en in j:
            query_original = en['text']
            query_escaped = query_original.replace(" ", "_")
            self.event_string_to_query_id_map[query_escaped] = query_escaped



    def query(self,event_string:str,entity_strings_or:typing.Set[str],entity_string_and:typing.Set[str]) -> typing.List[typing.List[str]]:

        query_id = self.event_string_to_query_id_map[event_string]

        doc_id_to_segments = dict()
        for segment_id in self.query_to_result.get(query_id,dict()).keys():
            doc_id = segment_id.split("-")[0]
            doc_id_to_segments.setdefault(doc_id,set()).add("-".join(segment_id.split("-")[:3]))
        ret = list()

        manager = multiprocessing.Manager()

        with manager.Pool(processes=multiprocessing.cpu_count()-1) as pool:
            worker = list()
            for doc_id,segments in doc_id_to_segments.items():
                worker.append(pool.apply_async(single_document_worker,args=(doc_id,self.doc_id_to_doc_list[doc_id],segments,entity_string_and,entity_strings_or)))
            for idx,i in enumerate(worker):
                i.wait()
                ret.extend(i.get())
        return ret


if __name__ == "__main__":
    import multiprocessing
    serifxml_list = "/home/hqiu/ld100/Hume_pipeline/Hume/expts/causeex_collab2_0913a_m24_shaved_dataset/event_consolidation_serifxml_out.list"
    shrinked_down_query_file = "/nfs/raid88/u10/users/hqiu/tmp/clir_baseline.110619.filtered"
    # input_json_path = "/home/hqiu/Public/parsed_collab.modified.json"
    input_json_path = "/home/hqiu/Public/structure_query_dryrun_110619.json"

    searcher = CLIRSearcher(serifxml_list,shrinked_down_query_file,input_json_path)

    with open(input_json_path) as fp:
        query_dict = json.load(fp)

    # for original_query_str,v in query_dict.items():
    #     print("## Querying: {}".format(original_query_str))
    #     for res in searcher.query(v[0],set(v[1]),set(v[2]))[:20]:
    #         print(res)
    #     print("## End Querying: {}".format(original_query_str))

    for en in query_dict:
        query_original = en['text']
        query_escaped = query_original.replace(" ", "_")
        entities = set(i['canonical_name'] for i in en['entity_mentions'])
        print("## Querying: {}".format(query_original))
        for res in searcher.query(query_escaped,entities,set()):
            print(res)
        print("## End Querying: {}".format(query_original))