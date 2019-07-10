#!/bin/bash

bin=+JSERIF_ROOT+/serif-util/target/appassembler/bin/AddEventMentionByPOSTags

strListSerifXmlFiles=+strListSerifXmlFiles+
strOutputDir=+strOutputDir+
file_whitelist=+file_whitelist+
file_blacklist=+file_blacklist+

mkdir $strOutputDir
sh $bin $strListSerifXmlFiles $strOutputDir $file_whitelist $file_blacklist
