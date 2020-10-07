package com.bbn.serif.util.events.consolidator;

import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Created by ychan on 10/8/19.
 */
public final class PrintEntityMentions {
  public static void main (String [] args) throws IOException {
    final String inputFilelist = args[0];
    final String outputFile = args[1];

    final ImmutableList<String>
        listStringFiles = Files.asCharSource(new File(inputFilelist), Charsets.UTF_8).readLines();

    List<File> filesToProcess = new ArrayList<File>();
    for(String strFile : listStringFiles)
      filesToProcess.add(new File(strFile));

    SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().build();

    List<String> lines = Lists.newArrayList();
    int docIndex = 0;
    for (final DocTheory dt : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
      for(int i=0; i<dt.numSentences(); i++) {
        final SentenceTheory st = dt.sentenceTheory(i);
        for(final Mention m : st.mentions()) {
          final String type = m.entityType().toString();
          final String text = m.span().tokenizedText().utf16CodeUnits().toString();
          lines.add(type + "\t" + text);
        }
      }

      docIndex += 1;
      if((docIndex % 100)==0) {
        System.out.println("Processed " + docIndex + " documents");
      }
    }

    Files.asCharSink(new File(outputFile), Charsets.UTF_8).writeLines(lines);
  }

}
