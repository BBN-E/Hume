package com.bbn.serif.util.events.consolidator;

import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.io.Files;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class PrintEventMentions {

  public static void main (String [] args) throws IOException {
    final String inputFilelist = args[0];
    final String outputFile = args[1];

    final ImmutableList<String>
        listStringFiles = Files.asCharSource(new File(inputFilelist), Charsets.UTF_8).readLines();

    List<File> filesToProcess = new ArrayList<File>();
    for(String strFile : listStringFiles)
      filesToProcess.add(new File(strFile));

    SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().build();

    final BufferedWriter writer = new BufferedWriter(new FileWriter(outputFile));

    //Multiset<String> eventAnchors = HashMultiset.create();
    int docIndex = 0;
    for (final DocTheory dt : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
      for(int i=0; i<dt.numSentences(); i++) {
        if(dt.sentenceTheory(i).isEmpty()) {
          continue;
        }
        final String sentenceText = dt.sentenceTheory(i).span().text().utf16CodeUnits().toString();
        for(final EventMention em : dt.sentenceTheory(i).eventMentions()) {
          final int phrase_start = em.semanticPhraseStart().get().intValue();
          final int phrase_end = em.semanticPhraseEnd().get().intValue();
          final String phrase_string = dt.sentenceTheory(i).tokenSequence().span(phrase_start, phrase_end).tokenizedText().utf16CodeUnits().toString();

          writer.write(phrase_string + '\n');
          /*
          final String eventType = em.type().asString();
          final String anchorText = em.anchorNode().span().text().toString().toLowerCase().replaceAll("\t'", "_").replaceAll(" ", "_");

          final SynNode anchorHead = em.anchorNode().head();
          final String headPOS = anchorHead.headPOS().asString();
          final String headText = anchorHead.tokenSpan().originalText().content().utf16CodeUnits().toLowerCase().replaceAll(" ", "_");

          writer.write("\n\nEVENT: " + eventType + "\t" + headText);
          writer.write("\n - " + sentenceText);

          for(final EventMention.Argument arg : em.arguments()) {
            final String role = arg.role().asString();
            final String argText = arg.span().text().utf16CodeUnits().toString();
            writer.write("\n - " + role + "\t" + argText);
          }
          */
        }
      }

      docIndex += 1;
      if((docIndex % 100)==0) {
        System.out.println("Processed " + docIndex + " documents");
      }
    }

    writer.close();
  }


}




