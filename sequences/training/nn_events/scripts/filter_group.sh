for i in `seq 1 12`
do
    #batch_dir=/nfs/raid87/u10/CauseEx/nn_models/annotation/annotation_01302019_full/batch_"$i"
    #batch_dir=/nfs/raid87/u10/CauseEx/nn_models/annotation/annotation_02042019_full/batch_"$i"
    batch_dir=/nfs/raid87/u10/CauseEx/nn_models/annotation/annotation_02062019_full/batch_"$i"
    echo "$batch_dir"
    python filter_serif_sentence.py "$batch_dir/argument.span_serif_list" "$batch_dir/argument.sent_spans" "$batch_dir/serifxml" "$batch_dir/argument.abridged.span_serif_list"
done
