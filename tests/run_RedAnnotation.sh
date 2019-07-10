#!/bin/bash

source_filename="/nfs/mercury-05/u34/shared/red/data/source/deft/NYT_ENG_20130603.0111"
annotation_filename="/nfs/mercury-05/u34/shared/red/data/annotation/deft/NYT_ENG_20130603.0111.RED-Relation.gold.completed.xml"

brat_filename="/tmp/a.ann"
text_filename="/tmp.a.txt"

python ../util/python/datasets/RedAnnotation.py $source_filename $annotation_filename $brat_filename $text_filename
