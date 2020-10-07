#!/bin/bash

set -e

ls +indir+/ | grep ".input_token" | sed "s/.input_token//g" | while read docid; do
  read max_seq <+indir+/"$docid".max_seq
  if (($max_seq > 0)); then
    PYTHONPATH=+bert_repo+ +python+ +bert_repo+/extract_features.py --input_file=+indir+/"$docid".input_token --output_file=+outdir+/"$docid" --vocab_file=+bert_model+/vocab.txt --bert_config_file=+bert_model+/bert_config.json --init_checkpoint=+bert_model+/bert_model.ckpt --max_seq_length="$max_seq" --layers=+bert_layers+ --batch_size=8
  fi
done
