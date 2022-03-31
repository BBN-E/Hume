import os
import stat
import gzip
import json
import annoy
import logging

logger = logging.getLogger(__name__)


class Span(object):
    def __init__(self, start_offset, end_offset):
        self.start_offset = int(start_offset)
        self.end_offset = int(end_offset)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.start_offset == other.start_offset and self.end_offset == other.end_offset

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return (self.__class__.__name__, self.start_offset, self.end_offset).__hash__()

    def __str__(self):
        return (self.start_offset, self.end_offset).__str__()

    def __repr__(self):
        return self.__str__()


class TokenIdxSpan(Span):
    pass


class EventMentionInstanceIdentifierTokenIdxBase(object):
    def __init__(self, doc_id, sentence_id, trigger_idx_span, original_text=None):
        self.doc_id = doc_id
        self.sentence_id = int(sentence_id)
        assert isinstance(trigger_idx_span, TokenIdxSpan)
        self.trigger_idx_span = trigger_idx_span
        self.original_text = original_text

    def __eq__(self, other):
        if not isinstance(other, EventMentionInstanceIdentifierTokenIdxBase):
            return False
        return self.doc_id == other.doc_id and \
               self.sentence_id == other.sentence_id and \
               self.trigger_idx_span == other.trigger_idx_span

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return (self.doc_id, self.sentence_id, self.trigger_idx_span).__hash__()

    def reprJSON(self):
        return {
            'docId': self.doc_id,
            'sentenceId': self.sentence_id,
            'triggerSentenceTokenizedPosition': self.trigger_idx_span.start_offset,
            'triggerSentenceTokenizedEndPosition': self.trigger_idx_span.end_offset,
            'originalText': self.original_text
        }

    def __repr__(self):
        return self.reprJSON().__repr__()

    def __str__(self):
        return self.reprJSON().__str__()

    @staticmethod
    def fromJSON(instance_identifier_token_idx_base_dict):
        doc_id = instance_identifier_token_idx_base_dict['docId']
        sentence_id = instance_identifier_token_idx_base_dict['sentenceId']
        trigger_tokenized_start_idx = instance_identifier_token_idx_base_dict['triggerSentenceTokenizedPosition']
        trigger_tokenized_end_idx = instance_identifier_token_idx_base_dict['triggerSentenceTokenizedEndPosition']
        original_text = instance_identifier_token_idx_base_dict['originalText']
        return EventMentionInstanceIdentifierTokenIdxBase(doc_id, sentence_id, TokenIdxSpan(trigger_tokenized_start_idx,
                                                                                            trigger_tokenized_end_idx),
                                                          original_text)

    @staticmethod
    def from_short_id_str(short_id_str):
        fields = short_id_str.split("|")
        if len(fields) == 4:
            doc_id, sent_id, start_token_idx, end_token_idx = fields
            return EventMentionInstanceIdentifierTokenIdxBase(doc_id, sent_id,
                                                              TokenIdxSpan(start_token_idx, end_token_idx))
        elif len(fields) == 5:
            doc_id, sent_id, start_token_idx, end_token_idx, original_text_json = fields
            # original_text = json.loads(original_text_json)["text"]
            # commented out the above as I think original_text_json is just a simple string
            # This might break find_nearest_ontology_neighbors.py:cbc_cluster_reader() method which also invokes this method, but is expecting a JSON dict as original_text_json
            return EventMentionInstanceIdentifierTokenIdxBase(doc_id, sent_id,
                                                              TokenIdxSpan(start_token_idx, end_token_idx),
                                                              original_text_json)

    def to_short_id_str(self):
        if self.original_text is not None:
            return "{}|{}|{}|{}|{}".format(self.doc_id, self.sentence_id,
                                           self.trigger_idx_span.start_offset,
                                           self.trigger_idx_span.end_offset,
                                           self.original_text)
        else:
            return "{}|{}|{}|{}".format(self.doc_id, self.sentence_id,
                                        self.trigger_idx_span.start_offset,
                                        self.trigger_idx_span.end_offset)


def read_event_mention_instance_identifier_list(filepath):
    em_list = list()
    with open(filepath, 'r', encoding='utf-8') as fp:
        for line in fp:
            em_list.append(EventMentionInstanceIdentifierTokenIdxBase.from_short_id_str(line.strip()))
    return em_list


def cbc_cluster_reader(cbc_cluster_path):
    cluster_id_to_records = dict()
    with open(cbc_cluster_path) as fp:
        for idx, i in enumerate(fp):
            i = i.strip()
            cluster_id, _, *rest = i.split(" ")
            for guest_node in rest:
                en = EventMentionInstanceIdentifierTokenIdxBase.from_short_id_str(guest_node)
                cluster_id_to_records.setdefault(cluster_id, set()).add(en)
    return cluster_id_to_records


def cbc_cluster_words_reader(cbc_cluster_path):
    cluster_id_to_words = dict()
    with open(cbc_cluster_path) as fp:
        for i in fp:
            i = i.strip()
            cluster_id, _, *rest = i.split(" ")
            for word in rest:
                cluster_id_to_words.setdefault(cluster_id, set()).add(word)
    return cluster_id_to_words


def reading_cbc_s3_trigger_info(cbc_s3_trigger_info_path):
    ret = list()
    with open(cbc_s3_trigger_info_path) as fp:
        for i in fp:
            i = i.strip()
            j = json.loads(i)
            ret.append(j)
    return ret


def sentence_jsonl_reader(sentence_jsonl_path):
    doc_id_sent_id_to_en = dict()
    with open(sentence_jsonl_path) as fp:
        for i in fp:
            i = i.strip()
            i = json.loads(i)
            doc_id = i['docId']
            sentence_id = i['sentenceId']
            doc_id_sent_id_to_en[(doc_id, sentence_id)] = i
    return doc_id_sent_id_to_en


def trigger_frequency_filter(cbc_s3_trigger_info, threshold):
    count_map = dict()
    print("Starting filtering trigger by threshold {}".format(threshold))
    for j in cbc_s3_trigger_info:
        j['docId'] = str(j['docId'])
        j['sentenceId'] = j['sentenceId']
        count_map[(j['trigger'], j['triggerPosTag'])] = count_map.get((j['trigger'], j['triggerPosTag']), 0) + 1
    ret_set = set()
    for word_tuple, cnt in count_map.items():
        if cnt >= threshold:
            ret_set.add(word_tuple)
    print("Finish filtering trigger")
    return ret_set


def build_doc_id_to_path_mapping(list_path, suffix=".xml"):
    ret = dict()
    with open(list_path) as fp:
        for i in fp:
            i = i.strip()
            doc_id = os.path.basename(i)
            doc_id = doc_id[:-len(suffix)]
            ret[doc_id] = i
    return ret


def read_saliency_list(saliency_list_path):
    salient_terms = dict()
    if saliency_list_path is not None:
        with open(saliency_list_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                fields = line.strip().split('\t')
                word_string = fields[0].replace(' ', '_')
                score = float(fields[1])
                salient_terms[word_string.lower()] = score
    return salient_terms


class StaticWordEmbCache(object):
    def __init__(self, word_to_vec, missing_token):
        self.word_to_vec = word_to_vec
        self.missing_token = missing_token

    def get_npz_for_text(self, text):
        if text in self.word_to_vec:
            return self.word_to_vec[text]
        else:
            logger.warning("Missing {} in word_to_vec".format(text))
            if self.missing_token is not None:
                return self.word_to_vec[self.missing_token]
            else:
                return None


class AnnoyCacheAdapter(object):
    @staticmethod
    def build_annoy_index(doc_id_to_records, bert_cache, statics_emb_cache, output_dir):
        os.makedirs(output_dir, exist_ok=True)

        annoy_ins = None
        idx_line = 0
        dimension = 0
        if bert_cache is not None and statics_emb_cache is not None:
            raise ValueError("We can only support either bert or statics embs but not both")
        added_text_for_statics_embs = set()
        with gzip.open(os.path.join(output_dir, 'id_map.jsonl.gz'), 'wt') as wfp:
            for idx, doc_id in enumerate(doc_id_to_records.keys()):
                logger.info("Handling ({}/{})".format(idx + 1, len(doc_id_to_records.keys())))
                ens = doc_id_to_records[doc_id]
                for en in ens:
                    if bert_cache is not None:
                        emb = bert_cache.get_contextual_emb_for_span(doc_id, en.sentence_id,
                                                                     en.trigger_idx_span.start_offset,
                                                                     en.trigger_idx_span.end_offset)
                        if emb is not None:
                            dimension = len(emb)
                            if annoy_ins is None:
                                annoy_ins = annoy.AnnoyIndex(dimension, "angular")
                                annoy_ins.on_disk_build(os.path.join(output_dir, "cache.bin.ann"))
                                os.chmod(os.path.join(output_dir, "cache.bin.ann"),
                                         stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                            annoy_ins.add_item(idx_line, emb)
                            idx_line += 1
                            wfp.write("{}\n".format(json.dumps(en.reprJSON(), ensure_ascii=False)))
                    elif statics_emb_cache is not None:
                        if en.original_text is None or en.original_text in added_text_for_statics_embs:
                            continue
                        emb = statics_emb_cache.get_npz_for_text(en.original_text)
                        if emb is not None:
                            dimension = len(emb)
                            if annoy_ins is None:
                                annoy_ins = annoy.AnnoyIndex(dimension, "angular")
                                annoy_ins.on_disk_build(os.path.join(output_dir, "cache.bin.ann"))
                                os.chmod(os.path.join(output_dir, "cache.bin.ann"),
                                         stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                            annoy_ins.add_item(idx_line, emb)
                            idx_line += 1
                            wfp.write("{}\n".format(json.dumps(en.reprJSON(), ensure_ascii=False)))
                        added_text_for_statics_embs.add(en.original_text)
        logger.info("Begin building annoy index")
        annoy_ins.build(100)
        # logger.info("Begin saving annoy index")
        # annoy_ins.save(
        #     os.path.join(output_dir, "cache.bin.ann"))
        logger.info("Finish saving annoy index")
        with open(os.path.join(output_dir, 'dimension'), 'w') as wfp:
            wfp.write("{}".format(dimension))
