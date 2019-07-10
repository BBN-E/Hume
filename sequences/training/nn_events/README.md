1) Pull the annotation data from the HAT system:
Path to anaconda install used for database session dumper:

`/nfs/ld100/u10/hqiu/venv/customized-event/bin`

Anaconda environment: `customized-event`

Example:

`LD_LIBRARY_PATH=/home/hqiu/lib python3 /home/hqiu/ld100/hume_causeex_adj/HAT/backend/tmp/dump_session_table_out_with_event_type_id_change_joshua.py --care_list /nfs/raid87/u10/CauseEx/nn_models/annotation/annotation_02062019.full.list --output_dir /nfs/raid87/u10/CauseEx/nn_models/annotation/annotation_02062019_full`

This puts the annotation data into a format acceptable by nlplingo, separated into batches that are trained independantly

2) Once we have the batches we want to filter out the from the documents on the annotated sentences.

Edit the script below to use the appropriate `$batch_dir`

`scripts/filter_group.sh`

and then execute to perform filtering on each batch dir.

The `filter_group.sh` uses this script 
`scripts/filter_serif_sentence.py`

3) With the data prepared we can perform parameter searching using this runjobs script

Example:

`run_causeex_trigger_train_parameter_search.pl params/parameter_search.params -sge`

4) Once the best parameters are determined the params_final file is modified to reflect those paramters

Then a runjobs script is ran to train with the entire data.

Example:

`run_causeex_trigger_train_final.pl params/train_final.params -sge`


