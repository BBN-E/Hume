import argparse
from collections import namedtuple
from datetime import datetime
import os
import numpy as np

import torch
from torch.utils.data import DataLoader, Dataset

from transformers import AutoTokenizer, DistilBertModel

import serifxml3 as serifxml

now = datetime.now()
current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)


class EncoderModel(object):
    """
    Parent class to:
    * InterSentenceModel (2 spans each with their own focus)
    * SingleFocusModel (a single span with a single focus)
    """
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.encoder_name = 'distilbert-base-uncased'

        self.encoder_dim = 1024 if '-large' in self.encoder_name else 768

        self.tokenizer = AutoTokenizer.from_pretrained(config['model_dir'], cache_dir=config['cache_dir'], do_lower_case=True, local_files_only=True)
        self.encoder = DistilBertModel.from_pretrained(config['model_dir'], cache_dir=self.config['cache_dir'], output_hidden_states=True, local_files_only=True)

        if self.config['device'].type != "cuda":
            try:
                self.encoder = torch.quantization.quantize_dynamic(self.encoder, {torch.nn.Linear}, dtype=torch.qint8)
            except RuntimeError:
                # skip quantization if it's not available
                pass
        self.encoder.to(config['device'])

    def _compute_span_reprs(self, word_reprs, token_starts, token_ends):
        """ If a span (as defined by token_starts and token_ends) consist of multiple words, we average the embeddings across those words''

        word_reprs.shape: [batch size, num words, word dim]
        span_idxs.shape: [batch size, num spans, 2]
        """
        batch_span_reprs = []
        batch_size, _, _ = word_reprs.shape
        for bid in range(batch_size):
            span_reprs = []
            start = token_starts[bid]
            end = token_ends[bid]
            words = word_reprs[bid][start: end]  # [span size, word dim]
            batch_span_reprs.append(torch.mean(words, dim=0))
        batch_span_reprs = torch.stack(batch_span_reprs, dim=0)  # [batch size, num spans, word dim]

        # word_reprs.size() = torch.Size([8, 63, 1024])     [batch_size, max num# words in batch, encoding_dim]
        # batch_span_reprs.size() = torch.Size([8, 1024])   [batch_size, encoding_dim]
        return batch_span_reprs

    def _token_lens_to_idxs(self, token_lens):
        """
        E.g. of token_lens:
        [ [2, 1, 1, 2, ...],
          [1, 1, 2, 2, ..., 1],
          [1, 4, 2]]
        For each sentence, a list of: the number of subwords for each token
        """
        max_token_num = max([len(x) for x in token_lens])  # number of tokens in the longest sentence, in this batch
        max_token_len = max([max(x) for x in token_lens])  # max number of subwords, over all tokens in this batch
        idxs = []
        for seq_token_lens in token_lens:
            # type(seq_token_lens)=list[int] , len of list=num# tokens in that sentence, and each element is num# subwords for that token
            seq_idxs = []
            offset = 0
            for token_len in seq_token_lens:  # token_len = num# subwords for that token
                seq_idxs.append([offset, offset + token_len])
                offset += token_len
            seq_idxs.extend([[-1, 0]] * (max_token_num - len(seq_token_lens)))
            idxs.append(seq_idxs)
        return idxs, max_token_num, max_token_len

    def _compute_word_reps_avg(self, piece_reprs, component_idxs):
        """ If a word is divided into multiple subwords, this will average their embeddings
        piece_reprs.shape: [batch size, max length, rep dim]
        component_idxs.shape: [batch size, num words, 2]
        """
        batch_word_reprs = []
        batch_size, _, _ = piece_reprs.shape
        _, num_words, _ = component_idxs.shape
        for bid in range(batch_size):
            word_reprs = []  # representation for each token. If a token is tokenized into multiple subwords, the following torch.mean will average the embeddings
            for wid in range(num_words):
                wrep = torch.mean(piece_reprs[bid][component_idxs[bid][wid][0]: component_idxs[bid][wid][1]], dim=0)
                word_reprs.append(wrep)
            word_reprs = torch.stack(word_reprs, dim=0)  # [num words, rep dim]
            batch_word_reprs.append(word_reprs)
        batch_word_reprs = torch.stack(batch_word_reprs, dim=0)  # [batch size, num words, rep dim]
        return batch_word_reprs

    def encode(self, piece_idxs, attention_masks, token_lens):
        """Encode input sequences.
        Get the embeddings of each word. If a word consists of multiple subwords, we average embeddings of those subwords.

        :param piece_idxs (LongTensor): word pieces indices
        :param attention_masks (FloatTensor): attention mask
        :param token_lens (list): For each sentence, a list of: the number of subwords for each token

        returns: [batch size, num words, rep dim] , where num_words = max num# words, over all examples/sentences in this batch
        """
        batch_size, _ = piece_idxs.size()   # [batch_size, max_sentence_length]
        all_encoder_outputs = self.encoder(piece_idxs, attention_mask=attention_masks)
        encoder_outputs = all_encoder_outputs[0]

        idxs, token_num, token_len = self._token_lens_to_idxs(token_lens)
        # token_num : in this batch, the num# of tokens in the longest sentence
        # token_len : over all the tokens, the max number of subwords
        # E.g. of idxs : [[[0, 2], [2, 3], ..., [-1, 0]], [[0, 2], [2, 3], ..., [-1, 0]]]
        #  * for each token in each sentence, the (start, end) subword index
        #  * e.g. [0, 2] means that this token consists of 2 subwords
        #  * the [-1, 0] are place holders, because we want each list to be the same length as `token_num`
        # If max_token_num=63 and max_token_len=4, then e.g. idxs.size()= torch.Size([8, 63, 2])

        idxs = piece_idxs.new(idxs) + 1
        # create a new 'idxs' with:
        # * same contents as old 'idxs', but add 1 to all contents (I believe the +1 is due to toknizer placing [CLS] in front of all sequences
        # * with same Datatype and on same device as piece_idxs

        # if a word is divided into multiple subwords, this will average their embeddings
        encoder_outputs = self._compute_word_reps_avg(encoder_outputs, idxs)
        # [batch size, num words, rep dim]

        #encoder_outputs = self.encoder_dropout(encoder_outputs)
        return encoder_outputs

    def scores(self, encoder_outputs, token_starts, token_ends):
        batch_size, _, encoder_dim = encoder_outputs.size()  # [batch_size, max num# words in this batch, encoding_dim]

        # m1 might consist of multiple words. If so, we will average the embeddings
        m_reprs = self._compute_span_reprs(encoder_outputs, token_starts, token_ends)
        # torch.Size([8, 1024])   [batch_size, encoding_dim]

        label_type_scores = self.label_type_ffn(m_reprs)

        return label_type_scores

    def get_embeddings(self, batch):
        word_reprs = self.encode(
            batch.piece_idxs,
            batch.attention_masks,
            batch.token_lens
        )
        return word_reprs


span_instance_fields = [
    'doc_id',
    'sent_id',
    'tokens',
    'piece_idxs',
    'attention_mask',
    'token_lens'
]

span_batch_fields = [
    'doc_ids',
    'sent_ids',
    'tokens',
    'piece_idxs',
    'attention_masks',
    'token_lens'
]

SpanInstance = namedtuple('SpanInstance', field_names=span_instance_fields)
SpanBatch = namedtuple('SpanBatch', field_names=span_batch_fields)

class EncodingDataset(Dataset):
    def __init__(self, data, config):
        self.config = config
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def numerize_token_seq(self, tokens, tokenizer):
        s_pieces = []
        for t in tokens:
            word_tokens = tokenizer.tokenize(t)
            if len(word_tokens) == 0:
                word_tokens = tokenizer.tokenize('_')
            s_pieces.append(word_tokens)
        #s_pieces = [tokenizer.tokenize(t) for t in tokens]

        # print ("s_pieces: {}".format(str(s_pieces)))
        s_token_lens = [len(x) for x in s_pieces]
        if 0 in s_token_lens:
            return None
        s_pieces = [p for ps in s_pieces for p in ps]
        if len(s_pieces) == 0:
            return None

        # Pad word pieces with special tokens
        piece_idxs = tokenizer.encode(
            s_pieces,
            add_special_tokens=True,
            max_length=self.config['max_sent_length']
        )
        if len(piece_idxs) > self.config['max_sent_length']:
            return None

        if self.config['batch_size'] > 1:
            pad_num = self.config['max_sent_length'] - len(piece_idxs)
        else:
            pad_num = 0

        attn_masks = [1] * len(piece_idxs) + [0] * pad_num
        piece_idxs = piece_idxs + [0] * pad_num
        if len(piece_idxs) == 0:
            return None

        return piece_idxs, attn_masks, s_token_lens

    def numberize(self, tokenizer):
        """Numberize word pieces, labels, etcs.
        :param tokenizer: Bert tokenizer.
        """
        data = []
        for inst_index, inst in enumerate(self.data):
            piece_idxs, attn_masks, s_token_lens = self.numerize_token_seq(
                inst["tokens"],
                tokenizer
            )

            if piece_idxs is None or attn_masks is None or s_token_lens is None:
                continue

            instance = SpanInstance(
                doc_id=inst['doc_id'],
                sent_id=inst['sent_id'],
                tokens=inst['tokens'],
                piece_idxs=piece_idxs,
                attention_mask=attn_masks,
                token_lens=s_token_lens
            )
            data.append(instance)

        self.data = data

    def collate_fn(self, batch):
        doc_ids = [inst.doc_id for inst in batch]
        sent_ids = [inst.sent_id for inst in batch]

        batch_piece_idxs = []
        batch_attention_masks = []
        batch_token_lens = []

        for inst in batch:
            batch_piece_idxs.append(inst.piece_idxs)
            batch_attention_masks.append(inst.attention_mask)
            batch_token_lens.append(inst.token_lens)

        if self.config['device'].type == "cuda":
            batch_piece_idxs = torch.cuda.LongTensor(batch_piece_idxs)
            batch_attention_masks = torch.cuda.FloatTensor(batch_attention_masks)
        else:
            batch_piece_idxs = torch.LongTensor(batch_piece_idxs)
            batch_attention_masks = torch.FloatTensor(batch_attention_masks)

        return SpanBatch(
            doc_ids=doc_ids,
            sent_ids=sent_ids,
            tokens=[inst.tokens for inst in batch],
            piece_idxs=batch_piece_idxs,
            attention_masks=batch_attention_masks,
            token_lens=batch_token_lens
        )


def get_embeddings_for_serifxml(serif_doc, config, model, output_filepath):
    docid = serif_doc.docid

    doc_sentence_data = []
    for st_index, sentence in enumerate(serif_doc.sentences):
        if sentence.sentence_theories is None or len(sentence.sentence_theories) == 0:
            continue

        st = sentence.sentence_theories[0]
        if st.token_sequence is None or len(st.token_sequence) == 0:
            continue

        instance = {
            'doc_id': docid,
            'sent_id': st_index,
            'tokens': [token.text for token in st.token_sequence]
        }
        doc_sentence_data.append(instance)

    dataset = EncodingDataset(doc_sentence_data, config)
    dataset.numberize(model.tokenizer)

    dataloader = DataLoader(
        dataset,
        batch_size=config['batch_size'],
        shuffle=False,
        collate_fn=dataset.collate_fn
    )

    doc_id_to_sent_emb_pair = dict()
    for batch in dataloader:
        embeddings = model.get_embeddings(batch)    # [batch_size, max num# words in sentence in batch, 768]
        token_lens = [len(tokens) for tokens in batch.tokens]

        for i in range(len(token_lens)):
            token_len = token_lens[i]       # number of words/tokens in this sentence
            sentence_embeddings = embeddings[i][0:token_len]

            doc_id = batch.doc_ids[i]
            sent_id = batch.sent_ids[i]
            doc_id_to_sent_emb_pair.setdefault(doc_id, dict())[sent_id] = np.asarray(sentence_embeddings.detach().cpu())

    for doc_id in doc_id_to_sent_emb_pair.keys():
        number_of_sentence = max(doc_id_to_sent_emb_pair[doc_id].keys()) + 1
        embs = list()
        for idx in range(number_of_sentence):
            emb = doc_id_to_sent_emb_pair[doc_id].get(idx,np.asarray([], dtype=np.float32))
            embs.append(emb)
        np.savez_compressed(output_filepath, embeddings=np.asarray(embs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--serifxml_filelist', required=True)
    parser.add_argument('--outputdir', required=True)
    args = parser.parse_args()

    config = dict()
    config['max_sent_length'] = 128
    config['cache_dir'] = '/nfs/raid87/u10/shared/Hume/wm/distillbert/transformer_cache'
    config['model_dir'] = '/nfs/raid87/u10/shared/Hume/wm/distillbert/model'

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config['device'] = device

    if torch.cuda.is_available():
        print("Using CUDA")
        config['batch_size'] = 64
    else:
        print("Using CPU")
        config['batch_size'] = 1

    filepaths = []
    with open(args.serifxml_filelist, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            filepaths.append(line.strip())

    model = EncoderModel(config)
    #model.to(config['device'])
    
    now = datetime.now()
    print(now.strftime("%H:%M:%S"))

    for filepath in filepaths:
        serif_doc = serifxml.Document(filepath)
        output_filepath = os.path.join(args.outputdir, '{}.npz'.format(serif_doc.docid))
        get_embeddings_for_serifxml(serif_doc, config, model, output_filepath)

        now = datetime.now()
        print(now.strftime("%H:%M:%S"))

