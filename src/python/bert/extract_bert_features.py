import re, json, io, os, sys, glob, collections, time, gzip

import tensorflow as tf

flags = tf.flags

FLAGS = flags.FLAGS

import modeling
import tokenization

from extract_features import InputExample, InputFeatures, model_fn_builder, input_fn_builder, _truncate_seq_pair


Instance = collections.namedtuple('Instance',['doc_id','sent_id','batch_id','text'])

InsanceId = collections.namedtuple("InsanceId",['doc_id','sent_id','batch_id'])

def convert_examples_to_features(examples, tokenizer):
    """Loads a data file into a list of `InputBatch`s."""
    seq_length = 0

    # First pass, only calculate max seq length
    for (ex_index, example) in enumerate(examples):
        tokens_a = tokenizer.tokenize(example.text_a)
        seq_length = max(len(tokens_a) + 2, seq_length)
        tokens_b = None
        if example.text_b:
            tokens_b = tokenizer.tokenize(example.text_b)
            seq_length = max(len(tokens_a) + len(tokens_b) + 3, seq_length)
    seq_length = min(min(seq_length,FLAGS.max_seq_length+3),512)
    features = []
    for (ex_index, example) in enumerate(examples):
        tokens_a = tokenizer.tokenize(example.text_a)
        tokens_b = None
        if example.text_b:
            tokens_b = tokenizer.tokenize(example.text_b)
        if tokens_b:
            # Modifies `tokens_a` and `tokens_b` in place so that the total
            # length is less than the specified length.
            # Account for [CLS], [SEP], [SEP] with "- 3"
            _truncate_seq_pair(tokens_a, tokens_b, seq_length - 3)
        else:
            # Account for [CLS] and [SEP] with "- 2"
            if len(tokens_a) > seq_length - 2:
                tokens_a = tokens_a[0:(seq_length - 2)]

        # The convention in BERT is:
        # (a) For sequence pairs:
        #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
        #  type_ids: 0     0  0    0    0     0       0 0     1  1  1  1   1 1
        # (b) For single sequences:
        #  tokens:   [CLS] the dog is hairy . [SEP]
        #  type_ids: 0     0   0   0  0     0 0
        #
        # Where "type_ids" are used to indicate whether this is the first
        # sequence or the second sequence. The embedding vectors for `type=0` and
        # `type=1` were learned during pre-training and are added to the wordpiece
        # embedding vector (and position vector). This is not *strictly* necessary
        # since the [SEP] token unambiguously separates the sequences, but it makes
        # it easier for the model to learn the concept of sequences.
        #
        # For classification tasks, the first vector (corresponding to [CLS]) is
        # used as as the "sentence vector". Note that this only makes sense because
        # the entire model is fine-tuned.
        tokens = []
        input_type_ids = []
        tokens.append("[CLS]")
        input_type_ids.append(0)
        for token in tokens_a:
            tokens.append(token)
            input_type_ids.append(0)
        tokens.append("[SEP]")
        input_type_ids.append(0)

        if tokens_b:
            for token in tokens_b:
                tokens.append(token)
                input_type_ids.append(1)
            tokens.append("[SEP]")
            input_type_ids.append(1)

        input_ids = tokenizer.convert_tokens_to_ids(tokens)

        # The mask has 1 for real tokens and 0 for padding tokens. Only real
        # tokens are attended to.
        input_mask = [1] * len(input_ids)

        # Zero-pad up to the sequence length.
        while len(input_ids) < seq_length:
            input_ids.append(0)
            input_mask.append(0)
            input_type_ids.append(0)

        assert len(input_ids) == seq_length
        assert len(input_mask) == seq_length
        assert len(input_type_ids) == seq_length

        if ex_index < 5:
            tf.logging.info("*** Example ***")
            tf.logging.info("unique_id: %s" % (example.unique_id))
            tf.logging.info("tokens: %s" % " ".join(
                [tokenization.printable_text(x) for x in tokens]))
            tf.logging.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
            tf.logging.info("input_mask: %s" % " ".join([str(x) for x in input_mask]))
            tf.logging.info(
                "input_type_ids: %s" % " ".join([str(x) for x in input_type_ids]))

        features.append(
            InputFeatures(
                unique_id=example.unique_id,
                tokens=tokens,
                input_ids=input_ids,
                input_mask=input_mask,
                input_type_ids=input_type_ids))
    return features,seq_length


def read_examples(str_io):
    """Read a list of `InputExample`s from an input file."""
    examples = []
    unique_id = 0
    while True:
        line = tokenization.convert_to_unicode(str_io.readline())
        if not line:
            break
        line = line.strip()
        text_a = None
        text_b = None
        m = re.match(r"^(.*) \|\|\| (.*)$", line)
        if m is None:
            text_a = line
        else:
            text_a = m.group(1)
            text_b = m.group(2)
        examples.append(InputExample(unique_id=unique_id, text_a=text_a, text_b=text_b))
        unique_id += 1
    return examples


class BertModel(object):
    def __init__(self, BERT_BASE_DIR):
        self.BERT_BASE_DIR = BERT_BASE_DIR
        FLAGS.vocab_file = os.path.join(self.BERT_BASE_DIR, "vocab.txt")
        FLAGS.bert_config_file = os.path.join(self.BERT_BASE_DIR, "bert_config.json")
        FLAGS.init_checkpoint = os.path.join(self.BERT_BASE_DIR, "bert_model.ckpt")
        self.loaded = False
        self.estimator = None

    def predict(self, input_str_buf):
        assert self.loaded
        examples = read_examples(input_str_buf)

        features,seq_length = convert_examples_to_features(
            examples=examples, tokenizer=self.tokenizer)

        unique_id_to_feature = {}
        for feature in features:
            unique_id_to_feature[feature.unique_id] = feature

        input_fn = input_fn_builder(
            features=features, seq_length=seq_length)
        output_list = list()
        no_exception = True
        try:
            for result in self.estimator.predict(input_fn, yield_single_examples=True):
                unique_id = int(result["unique_id"])
                feature = unique_id_to_feature[unique_id]
                output_json = dict()
                output_json["linex_index"] = unique_id
                all_features = []
                for (i, token) in enumerate(feature.tokens):
                    all_layers = []
                    for (j, layer_index) in enumerate(self.layer_indexes):
                        layer_output = result["layer_output_%d" % j]
                        layers = dict()
                        layers["index"] = layer_index
                        layers["values"] = [
                            round(float(x), 6) for x in layer_output[i:(i + 1)].flat
                        ]
                        all_layers.append(layers)
                    features = dict()
                    # We don't need token. Save us some memory
                    # features["token"] = token
                    features["layers"] = all_layers
                    all_features.append(features)
                output_json["features"] = all_features
                output_list.append(output_json)
        except Exception:
            import traceback
            tf.logging.warn(traceback.format_exc())
            for i in range(len(examples)):
                output_json = dict()
                output_json["features"] = list()
                output_list.append(output_json)
            no_exception = False
        return output_list,no_exception

    def load_model(self):
        self.estimator = None
        self.loaded = False
        tf.logging.set_verbosity(tf.logging.ERROR)

        self.layer_indexes = [int(x) for x in FLAGS.layers.split(",")]
        bert_config = modeling.BertConfig.from_json_file(FLAGS.bert_config_file)
        self.tokenizer = tokenization.FullTokenizer(
            vocab_file=FLAGS.vocab_file, do_lower_case=FLAGS.do_lower_case)

        is_per_host = tf.contrib.tpu.InputPipelineConfig.PER_HOST_V2
        run_config = tf.contrib.tpu.RunConfig(
            master=FLAGS.master,
            tpu_config=tf.contrib.tpu.TPUConfig(
                num_shards=FLAGS.num_tpu_cores,
                per_host_input_for_training=is_per_host))

        model_fn = model_fn_builder(
            bert_config=bert_config,
            init_checkpoint=FLAGS.init_checkpoint,
            layer_indexes=self.layer_indexes,
            use_tpu=FLAGS.use_tpu,
            use_one_hot_embeddings=FLAGS.use_one_hot_embeddings)

        # If TPU is not available, this will fall back to normal Estimator on CPU
        # or GPU.
        self.estimator = tf.contrib.tpu.TPUEstimator(
            use_tpu=FLAGS.use_tpu,
            model_fn=model_fn,
            config=run_config,
            predict_batch_size=FLAGS.batch_size)
        self.loaded = True

def list_spliter_by_batch_size(my_list, batch_size):
    return [my_list[i * batch_size:(i + 1) * batch_size] for i in range((len(my_list) + batch_size - 1) // batch_size)]


def bert_extract_features_main(BERT_BASE_DIR,bucket_size,input_batch_file,output_dir,output_prefix,current_bert_batch_id):

    bert_model = BertModel(BERT_BASE_DIR)
    bert_model.load_model()
    sent_info_arr = list()
    sentences = list()
    containing_batch_ids = set()

    with open(input_batch_file) as fp:
        for input_dir in fp:
            input_dir = input_dir.strip()
            input_token_file = os.path.join(input_dir,"input_token.info")
            sent_info_file = os.path.join(input_dir,"sent_info.info")
            with gzip.open(sent_info_file,'rt') as fp:
                for i in fp:
                    i = i.strip()
                    j = json.loads(i)
                    instance_id = InsanceId(**j)
                    sent_info_arr.append(instance_id)
                    containing_batch_ids.add(instance_id.batch_id)

            with gzip.open(input_token_file,'rt') as rfp:
                for idx,sentence in enumerate(rfp):
                    sentences.append(Instance(sent_info_arr[idx].doc_id,sent_info_arr[idx].sent_id,sent_info_arr[idx].batch_id,json.loads(sentence)['text']))

    batch_id_to_file_path = dict()

    for batch_id in containing_batch_ids:
        batch_output_dir = os.path.join(output_dir,"{}{}".format(output_prefix,batch_id))
        os.makedirs(batch_output_dir,exist_ok=True)
        sent_info_path = os.path.join(batch_output_dir, "{}_sent_info.info".format(current_bert_batch_id))
        batch_id_to_file_path[batch_id] = sent_info_path
        with gzip.open(sent_info_path,'wt') as fp:
            pass

    sentences_in_buckets = list_spliter_by_batch_size(sentences,batch_size=bucket_size)

    sum_performance = 0
    cnt = 0
    for bucket in sentences_in_buckets:
        start_time = time.time()
        input_buf = io.StringIO("".join(i.text for i in bucket))
        input_buf.seek(0)
        output_list,no_exception = bert_model.predict(input_buf)
        if no_exception is False:
            # We send bert sentence by sentence
            tf.logging.warn("Fallback into single sentence per batch mode")
            output_list_all = list()
            input_buf.seek(0)
            for sentence in input_buf:
                input_buf_per_sentence = io.StringIO(sentence)
                input_buf_per_sentence.seek(0)
                output_list,_ = bert_model.predict(input_buf_per_sentence)
                output_list_all.extend(output_list)
            output_list = output_list_all
        assert len(bucket) == len(output_list)
        batch_id_to_entries = dict()
        for idx in range(len(bucket)):
            instance = bucket[idx]
            bert_obj_str = output_list[idx]
            batch_id_to_entries.setdefault(instance.batch_id,list()).append([instance,bert_obj_str])
        for batch_id,ens in batch_id_to_entries.items():
            with gzip.open(batch_id_to_file_path[batch_id], 'at') as fp:
                for instance,bert_obj_str in ens:
                    fp.write("{}\n".format(json.dumps({"doc_id":instance.doc_id,"sent_id":instance.sent_id,"bert_emb":bert_obj_str})))

        end_time = time.time()
        duration = end_time - start_time
        sum_performance += len(bucket) / duration
        cnt += 1
        tf.logging.warn("Max sequence length: {} , Bin size: {} , Batch size: {} , speed: {} sentences/sec , count: {} , ave : {} ".format(FLAGS.max_seq_length,bucket_size,FLAGS.batch_size, len(bucket) / duration,cnt,sum_performance/cnt))
        sys.stdout.flush()



if __name__ == "__main__":
    flags.DEFINE_string('input_batch_file',None,"")
    flags.DEFINE_string('output_dir',None,"")
    flags.DEFINE_string('output_prefix',None,"")
    flags.DEFINE_string('current_bert_batch_id',None,"")
    flags.DEFINE_string('BERT_BASE_DIR', None, "")
    flags.DEFINE_integer('bucket_size', 128, "")
    bert_extract_features_main(FLAGS.BERT_BASE_DIR, FLAGS.bucket_size, FLAGS.input_batch_file, FLAGS.output_dir,FLAGS.output_prefix,FLAGS.current_bert_batch_id)