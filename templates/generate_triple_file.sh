#!/bin/bash

set -e
expt_dir=+expt_dir+
triple_file=+triple_file+
all_input=$expt_dir/decoding/*.log.decoder.output.relations

# Check to make sure input exists
if [ `ls -1 $all_input 2>/dev/null | wc -l ` -gt 0 ];
then
    echo "Input found"
else
    echo "No input found! Exiting."
    exit 1
fi

cat $all_input|awk 'BEGIN{FS="\t"}{if(NF>7)print $1"\t"$(NF-2)"\t"$(NF-1)}'|sort|uniq -c|sort -r -n > $triple_file
