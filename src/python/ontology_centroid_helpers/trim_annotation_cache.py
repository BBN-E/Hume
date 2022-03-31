import argparse
import json
import logging
import numpy as np

from src.python.concept_discovery.embedding_caches import BertEmbeddingCache

logger = logging.getLogger(__name__)


def main(annotation_jsonl, embeddings_list, output_file):
    bert_cache = BertEmbeddingCache(embeddings_list)
    tokens_to_emb = dict()
    with open(annotation_jsonl) as fp:
        for i in fp:
            i = i.strip()
            en = json.loads(i)
            doc_id, sent_idx, trigger_start_idx, trigger_end_idx, event_type = en['docid'], en['sent_idx'], en[
                'trig_idx_start'], en['trig_idx_end'], en['event_type']
            for token_idx in range(trigger_start_idx, trigger_end_idx + 1):
                emb = bert_cache.get_contextual_emb_for_token(doc_id, sent_idx, token_idx)
                if emb is not None:
                    tokens_to_emb[(doc_id, sent_idx, token_idx)] = emb

    with open(output_file, 'wb') as fp:
        np.savez_compressed(fp, tokens_to_embeddings=tokens_to_emb)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--annotation-event-jsonl', required=True)
    parser.add_argument('--annotation-npz-list', required=True)
    parser.add_argument('--output-file', required=True)
    args = parser.parse_args()

    main(args.annotation_event_jsonl, args.annotation_npz_list, args.output_file)
