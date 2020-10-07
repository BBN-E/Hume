package com.bbn.serif.util.events.consolidator;

import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;

import com.google.common.base.Charsets;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import com.google.common.collect.Multiset;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class PrintEventTriggers {

  public static void main (String [] args) throws IOException {
    final String inputFilelist = args[0];
    final String outputFile = args[1];

    final ImmutableList<String>
        listStringFiles = Files.asCharSource(new File(inputFilelist), Charsets.UTF_8).readLines();

    List<File> filesToProcess = new ArrayList<File>();
    for(String strFile : listStringFiles)
      filesToProcess.add(new File(strFile));

    SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().build();

    Multiset<String> eventAnchors = HashMultiset.create();
    int docIndex = 0;
    for (final DocTheory dt : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
      for(int i=0; i<dt.numSentences(); i++) {
        final SentenceTheory st = dt.sentenceTheory(i);
        for(final EventMention em : st.eventMentions()) {
          final String eventType = em.type().asString();
          final String anchorText = em.anchorNode().span().text().toString().toLowerCase().replaceAll("\t'", "_").replaceAll(" ", "_");

          final SynNode anchorHead = em.anchorNode().head();
          final String headPOS = anchorHead.headPOS().asString();
          final String headText = anchorHead.tokenSpan().originalText().content().utf16CodeUnits().toLowerCase().replaceAll(" ", "_");

          final String prefix = st.tokenSequence().span(Math.max(0, anchorHead.span().startToken().index()-1), Math.max(0, anchorHead.span().startToken().index()-1)).tokenizedText().utf16CodeUnits().toString();
          final String suffix = st.tokenSequence().span(Math.min(anchorHead.span().endToken().index()+1, st.tokenSequence().size()-1), Math.min(anchorHead.span().endToken().index()+1, st.tokenSequence().size()-1)).tokenizedText().utf16CodeUnits().toString();

          eventAnchors.add(eventType + "\t" + prefix.toLowerCase().replaceAll(" ", "_") + "_" + anchorText.toLowerCase().replaceAll(" ", "_") + "_" + suffix.toLowerCase().replaceAll(" ", "_") + "\t" + headText.toLowerCase().replaceAll(" ", "_"));
        }
      }

      docIndex += 1;
      if((docIndex % 100)==0) {
        System.out.println("Processed " + docIndex + " documents");
      }
    }

    List<String> lines = Lists.newArrayList();
    for(final String key : eventAnchors.elementSet()) {
      final int count = eventAnchors.count(key);
      lines.add(key + "\t" + count);
    }

    Files.asCharSink(new File(outputFile), Charsets.UTF_8).writeLines(lines);
  }


}




