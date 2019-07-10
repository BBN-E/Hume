


from cyberlingo.common.utils import get_tokens_corresponding_to_span
from cyberlingo.common.utils import IntPair
from cyberlingo.common.utils import get_span_with_offsets
from cyberlingo.common.utils import get_spans_in_offsets
from cyberlingo.text.text_span import Token
from cyberlingo.text.text_span import Sentence
from cyberlingo.text.text_span import spans_overlap

class Document(object):
    """Represents a document
    """
    verbosity = 0

    def __init__(self, docid, text=None, sentence_strings=None):
        self.docid = docid
        self.text = text
        self.sentence_strings = sentence_strings    # sometimes you want to keep the strings separate, e.g. for ACE
        """:type: list[str]"""
        self.sentences = []
        """:type: list[text.text_span.Sentence]"""
        self.entity_mentions = []
        """:type: list[text.text_span.EntityMention]"""
        self.events = []
        """:type: list[text.text_theory.Event]"""

    def add_sentence(self, sentence):
        self.sentences.append(sentence)

    def add_entity_mention(self, entity_mention):
        self.entity_mentions.append(entity_mention)

    def add_event(self, event):
        self.events.append(event)

    def number_of_entity_mentions(self):
        return len(self.entity_mentions)

    def number_of_events(self):
        return len(self.events)


    def annotate_sentences(self, model, embeddings):
        """We use Spacy for model
        :type embeddings: embeddings.word_embeddings.WordEmbedding
        """
        #print('Let us first show the event annotations in this document')
        #for event in self.events:
        #    print(event.to_string())
        #print('==============')

        self.sentence_segmention_and_tokenization(model)
        for sent in self.sentences:
            self.annotate_sentence_with_word_embeddings(sent, embeddings)
            self.annotate_sentence_with_entity_mentions(sent)
            self.annotate_sentence_with_events(sent)
            #print(sent.text)
            #print('===Events===')
            #for event in sent.events:
            #    print(event.to_string())
        #exit(0)

        # print('==== Finished annotating sentences, printing from within text_theory.Document.annotate_sentences ====')
        # print('#document events={}'.format(len(self.events)))
        # for sent in self.sentences:
        #     sent.to_string()
        #     for e in sent.events:
        #         print('<Sentence-Events>')
        #         print(e.to_string())
        #         print('</Sentence-Events>')
        #     print('')
        # exit(0)


    def sentence_segmention_and_tokenization(self, model):
        """Whatever model we pass in, must be able to perform sentence segmentation and tokenization
        by calling model(self.text). We typically use Spacy
        """
        if self.text is not None:
            self.sentence_segmention_and_tokenization_with_text(model)
        elif self.sentence_strings is not None:
            self.sentence_segmention_and_tokenization_with_list(model)
        else:
            raise ValueError('text and sentence_strings are both None, this should not happen')

    def sentence_segmention_and_tokenization_with_text(self, model):
        """Whatever model we pass in, must be able to perform sentence segmentation and tokenization
        by calling model(self.text). We typically use Spacy
        """
        doc = model(self.text)

        for sent_index, sent in enumerate(doc.sents):
            tokens = []
            for token_index, token in enumerate(sent):
                start = token.idx
                end = token.idx + len(token.text)
                tokens.append(Token(IntPair(start, end), token.text, token, token_index))
            sentence = Sentence(self.docid, IntPair(sent.start_char, sent.end_char), sent.text.strip(), tokens, sent_index)
            self.sentences.append(sentence)

    def sentence_segmention_and_tokenization_with_list(self, model):
        """Whatever model we pass in, must be able to perform sentence segmentation and tokenization
        by calling model(self.text). We typically use Spacy
        """
        offset = 0
        for ss in self.sentence_strings:
            if len(ss) == 0 or ss.isspace():
                pass
            else:
                for sent in model(ss).sents:  # for each Spacy sentence
                    tokens = []
                    for token_index, token in enumerate(sent):
                        start = offset + token.idx
                        end = start + len(token.text)
                        tokens.append(Token(IntPair(start, end), token.text, token, token_index))
                    sentence = Sentence(self.docid,
                                        IntPair(offset + sent.start_char, offset + sent.start_char + len(sent.text)),
                                        sent.text.strip(), tokens, len(self.sentences))
                    self.sentences.append(sentence)
            offset += len(ss)

    def annotate_sentence_with_word_embeddings(self, sent, embeddings):
        """Annotate sentence tokens with word embeddings
        :type sent: text.text_span.Sentence
        :type embeddings: embeddings.word_embeddings.WordEmbedding
        """
        for token in sent.tokens:
            if token.is_punct is False:
                vector_text, index, vector = embeddings.get_vector(token)
                if vector_text:
                    token.vector_text = vector_text
                    token.vector_index = index
                    token.word_vector = vector
                    token.has_vector = True


    def annotate_sentence_with_entity_mentions(self, sent):
        """We assign entity mentions that are properly backed by tokens to the sentence
        :type sent: text.text_span.Sentence
        """

        # get the list of EntityMention in this sentence
        sent_em = self.get_entity_mentions_in_span(sent.start_char_offset(), sent.end_char_offset())
        for em in sent_em:
            em.with_tokens(get_tokens_corresponding_to_span(sent.tokens, em))
            if em.tokens is not None:
                sent.add_entity_mention(em)
            elif self.verbosity == 1:
                print('EntityMention not backed by tokens, dropping ', em.to_string())

    def annotate_sentence_with_events(self, sent):
        """For an event, anchors must be backed by tokens, and arguments must be backed by entity mentions
        :type sent: text.text_span.Sentence
        """
        #print('Sentence: ' , sent.text)
        event_counter = 0
        for event in self.events:
            # grab anchors and arguments that are within this sentence
            #print('checking against event ', event.to_string())
            anchors = event.get_anchors_in_span(sent.start_char_offset(), sent.end_char_offset())
            arguments = event.get_arguments_in_span(sent.start_char_offset(), sent.end_char_offset())
            #print('num# anchors in sentence=', len(anchors))
            #print('num# arguments in sentence=', len(arguments))

            valid_anchors = []
            for anchor in anchors:
                anchor.with_tokens(get_tokens_corresponding_to_span(sent.tokens, anchor))
                if anchor.tokens is not None:
                    valid_anchors.append(anchor)
                elif self.verbosity == 1:
                    print('Anchor not backed by tokens, dropping ', anchor.to_string())
                    #print('{}\n'.format(' '.join('{}:{}'.format(token.start_char_offset(), token.text) for token in sent.tokens)))

            valid_arguments = []
            for arg in arguments:
                em = get_span_with_offsets(sent.entity_mentions, arg.start_char_offset(), arg.end_char_offset())
                if em is not None:  # there is an EntityMention corresponding to the EventArgument
                    valid_arguments.append(arg.copy_with_entity_mention(em))
                elif self.verbosity == 1:
                    print('EventArgument not backed by EntityMention, dropping ', arg.to_string())

            if len(valid_anchors) > 0 or (len(valid_anchors) > 0 and len(valid_arguments) > 0):
                event_id = self.docid + '-s' + str(sent.index) + '-e' + str(event_counter)
                sent_event = Event(event_id, event.label)
                sent_event.add_anchors(valid_anchors)
                if len(valid_arguments) > 0:
                    sent_event.add_arguments(valid_arguments)
                sent.add_event(sent_event)
                event_counter += 1
                #print('Adding sent_event to sentence:', sent_event.to_string())


    def get_entity_mention_with_span(self, start, end):
        """Get the entity mention with the exact same given (start, end) span
        Returns:
            text.text_span.EntityMention
        """
        return get_span_with_offsets(self.entity_mentions, start, end)


    def get_entity_mentions_in_span(self, start, end):
        """Useful for getting all entity mentions in a sentence
        Returns:
            list[text.text_span.EntityMention]
        """
        return get_spans_in_offsets(self.entity_mentions, start, end)

    def get_entity_mention_with_id(self, id):
        for em in self.entity_mentions:
            if em.id == id:
                return em
        return None

    def to_string(self):
        outlines = []
        prefix = ('<DOC docid=%s>\n<TEXT>\n%s\n</TEXT>' % (self.docid, self.text))
        outlines.append(prefix)
        for sent in self.sentences:
            outlines.append('<Sentence index=%d text="%s">' % (sent.index, sent.text))
            outlines.append('TOKENS: %s' % (' '.join(token.text for token in sent.tokens)))
            for em in sent.entity_mentions:
                outlines.append(em.to_string())
            for e in sent.events:
                outlines.append(e.to_string())
        outlines.append('</DOC>')
        return '\n'.join(outlines)


class Event(object):
    """Annotation of an event. There is no explicit differentiation between event and event mention
    label: event type
    anchors: a list of text_span.Anchor , you can think of each anchor as an event mention
    arguments: a list of text_span.EventArgument
    """

    def __init__(self, id, label):
        self.id = id
        self.label = label
        self.anchors = []
        """:type: list[text.text_span.Anchor]"""
        self.arguments = []
        """:type: list[text.text_span.EventArgument]"""
        self.event_spans = []
        """:type: list[text.text_span.EventSpan]"""

    def add_anchor(self, anchor):
        self.anchors.append(anchor)

    def add_anchors(self, anchors):
        self.anchors.extend(anchors)

    def add_event_span(self, span):
        self.event_spans.append(span)

    def number_of_anchors(self):
        return len(self.anchors)

    def overlaps_with_anchor(self, span):
        """Check whether input span overlaps with any of our anchors
        :type anchor: text.text_span.Span
        """
        for a in self.anchors:
            if spans_overlap(span, a):
                return True
        return False

    def add_argument(self, argument):
        self.arguments.append(argument)

    def add_arguments(self, arguments):
        self.arguments.extend(arguments)

    def number_of_arguments(self):
        return len(self.arguments)

    def get_anchors_in_span(self, start, end):
        """Get the list of anchors within a given (start, end) character offset, e.g. within a sentence
        Returns:
            list[text.text_span.Anchor]
        """
        return get_spans_in_offsets(self.anchors, start, end)

    def get_arguments_in_span(self, start, end):
        """Get the list of arguments within a given (start, end) character offset, e.g. within a sentence
        Returns:
            list[text.text_span.EventArgument]
        """
        return get_spans_in_offsets(self.arguments, start, end)

    def event_from_span(self, start, end):
        """Generate a new event from given (start, end) character offsets, e.g. within a sentence
        Returns:
            text.text_theory.Event
        """
        event = Event(self.id, self.label)
        event.add_anchors(self.get_anchors_in_span(start, end))
        event.add_arguments(self.get_arguments_in_span(start, end))
        return event

    def get_role_for_entity_mention(self, entity_mention):
        """
        :type entity_mention: text.text_span.EntityMention
        """
        for arg in self.arguments:
            if entity_mention == arg.entity_mention:
                return arg.label
        return 'None'

    def to_string(self):
        anchor_strings = '\n'.join(a.to_string() for a in self.anchors)
        argument_strings = '\n'.join(a.to_string() for a in self.arguments)
        prefix = ('<Event id=%s type=%s>' % (self.id, self.label))
        return prefix + '\n#anchors=' + str(len(self.anchors)) + ' #args=' + str(len(self.arguments)) + '\n' + \
               anchor_strings + '\n' + argument_strings + '\n</Event>'

