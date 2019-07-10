#!/bin/bash

bin=+JSERIF_ROOT+/serif-util/target/appassembler/bin/RunEventConsolidator
strListSerifXmlFiles=+strListSerifXmlFiles+
strOutputDir=+strOutputDir+
strInputMetadataFile=+strInputMetadataFile+
compatibleEventFile=+compatibleEventFile+
ontologyFile=+ontologyFile+
argumentRoleEntityTypeFile=+argumentRoleEntityTypeFile+
mode=+mode+
keywordFile=+keywordFile+
lemmaFile=+lemmaFile+
copyArgumentSentenceWindow=+copyArgumentSentenceWindow+
blacklistFile=+blacklistFile+

wordnetDir=+wordnetDir+
sieveResourceDir=+sieveResourceDir+
geonamesFile=+geonamesFile+
polarityFile=+polarityFile+
kbpEventMappingFile=+kbpEventMappingFile+

accentEventMappingFile=+accentEventMappingFile+
accentCodeToEventTypeFile=+accentCodeToEventTypeFile+ 

mkdir $strOutputDir

sh $bin $strListSerifXmlFiles $strOutputDir $strInputMetadataFile aggressive-only-for-news $compatibleEventFile $ontologyFile $argumentRoleEntityTypeFile $keywordFile $lemmaFile $mode $copyArgumentSentenceWindow $blacklistFile $wordnetDir $sieveResourceDir $geonamesFile $polarityFile $kbpEventMappingFile $accentEventMappingFile $accentCodeToEventTypeFile
