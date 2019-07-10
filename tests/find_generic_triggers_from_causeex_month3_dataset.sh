#!/bin/bash

trigger_file=causeex-month3.triggers.txt

# cat /nfs/mercury-05/u34/CauseEx/ychan/expts/causeex-month3-generic-trigger/triggerfinder/chunk-*/* > $trigger_file

cat $trigger_file | awk '{print $1}'|sort|uniq -c|sort -r -n > $trigger_file.freq
