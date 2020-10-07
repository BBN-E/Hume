#!/bin/bash

bin=+bin+

strListSerifXmlFiles=+strListSerifXmlFiles+
strOutputDir=+strOutputDir+
file_whitelist=+file_whitelist+
file_blacklist=+file_blacklist+

mkdir $strOutputDir
sh $bin $strListSerifXmlFiles $strOutputDir $file_whitelist $file_blacklist
