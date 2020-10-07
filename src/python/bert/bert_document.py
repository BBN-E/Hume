import codecs


class TokenWithIndex(object):
    def __init__(self, text, sentence_index, token_index):
        self.text = text
        self.sentence_index = sentence_index
        self.token_index = token_index


class BertDocument(object):
    def __init__(self, docid, sentences_input_tokens, maximum_allowed_bert_tokens_per_sentence):
        """
        :type docid: str
        :type sentences_input_tokens: list[list[TokenWithIndex]]
        """
        self.docid = docid
        self.sentences_input_tokens = sentences_input_tokens
        self.sentences_bert_tokens = []  # for each sentence, its bert tokens
        self.sentences_token_map = []  # for each sentence, the int-int mapping of input-to-bert tokens
        self.max_seq_length = 0  # max number of BERT tokens in any sentence
        self.maximum_allowed_bert_tokens_per_sentence = maximum_allowed_bert_tokens_per_sentence

    def to_bert_tokens(self, input_tokens, tokenizer):
        """
        :type input_tokens: list[str]
        """
        bert_tokens = []
        input_to_bert_map = []  # int->int mapping between input_tokens and bert_tokens

        bert_tokens.append('[CLS]')
        for input_token in input_tokens:
            input_to_bert_map.append(len(bert_tokens))
            bert_tokens.extend(tokenizer.tokenize(input_token))
        bert_tokens.append('[SEP]')

        return (bert_tokens, input_to_bert_map)

    def tokenize_all_sentences(self, tokenizer):
        for sent_index, sentence_tokens in enumerate(self.sentences_input_tokens):
            tokens_texts = [token.text for token in sentence_tokens]
            bert_tokens, input_to_bert_map = self.to_bert_tokens(tokens_texts, tokenizer)

            bert_tokens = list(bert_tokens)[
                          :self.maximum_allowed_bert_tokens_per_sentence]
            for token_cutoff in range(len(input_to_bert_map)):
                if (input_to_bert_map[token_cutoff]
                        >= self.maximum_allowed_bert_tokens_per_sentence):
                    input_to_bert_map = input_to_bert_map[:token_cutoff]
                    break

            # assert len(tokens_texts) == len(input_to_bert_map) # This no longer valid
            self.sentences_bert_tokens.append(bert_tokens)
            self.sentences_token_map.append(input_to_bert_map)
            if len(bert_tokens) > self.max_seq_length:
                self.max_seq_length = len(bert_tokens)

    def write_input_tokens(self, outfilepath):
        with codecs.open(outfilepath, 'w', encoding='utf-8') as o:
            for tokens in self.sentences_input_tokens:
                o.write(' '.join([token.text for token in tokens]))
                o.write('\n')

    def write_bert_tokens(self, outfilepath):
        # by default, we do not write out the [CLS] and [SEP]
        with codecs.open(outfilepath, 'w', encoding='utf-8') as o:
            for tokens in self.sentences_bert_tokens:
                o.write(' '.join(tokens[1:-1]))
                o.write('\n')

    def write_token_map(self, outfilepath):
        with codecs.open(outfilepath, 'w', encoding='utf-8') as o:
            for token_map in self.sentences_token_map:
                o.write(' '.join([str(index) for index in token_map]))
                o.write('\n')

    def write_max_seq_length(self, outfilepath):
        with codecs.open(outfilepath, 'w', encoding='utf-8') as o:
            o.write(str(self.max_seq_length))
            o.write('\n')
