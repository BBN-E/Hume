#!/bin/bash

bin=+JSERIF_ROOT+/serif-util/target/appassembler/bin/AddEventMentionFromJson

inputFileJson=+inputFileJson+
inputListSerifXmls=+inputListSerifXmls+
outputDir=+outputDir+

sh $bin $inputFileJson $inputListSerifXmls $outputDir

