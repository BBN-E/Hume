package com.bbn.serif.util.events.consolidator;

import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMultiset;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class FindCrossBorderMovement {


  private static ImmutableMultiset<String> extractKeywords(final DocTheory dt, final ImmutableSet<String> keywords, boolean toLowerCase) {
    final ImmutableMultiset.Builder<String> ret = ImmutableMultiset.builder();

    for(int i=0; i<dt.numSentences(); i++) {
      if(dt.sentenceTheory(i).isEmpty()) {
        continue;
      }

      String sentenceText = " " + dt.sentenceTheory(i).span().tokenizedText().utf16CodeUnits().toString() + " ";
      if(toLowerCase) {
        sentenceText = sentenceText.toLowerCase();
      }
      for(final String kw : keywords) {
        String currentKw = " " + kw + " ";
        if(toLowerCase) {
          currentKw = kw.toLowerCase();
        }

        if(sentenceText.indexOf(currentKw)!=-1) {
          ret.add(kw);
        }
      }
    }

    return ret.build();
  }

  private static int countKeywordFrequency(final DocTheory dt, final ImmutableSet<String> keywords, boolean toLowerCase) {
    int freq = 0;

    for(int i=0; i<dt.numSentences(); i++) {
      if(dt.sentenceTheory(i).isEmpty()) {
        continue;
      }

      String sentenceText = " " + dt.sentenceTheory(i).span().tokenizedText().utf16CodeUnits().toString() + " ";
      if(toLowerCase) {
        sentenceText = sentenceText.toLowerCase();
      }
      for(final String kw : keywords) {
        String currentKw = kw;
        if(toLowerCase) {
          currentKw = kw.toLowerCase();
        }

        if(sentenceText.indexOf(currentKw)!=-1) {
          freq += 1;
        }
      }
    }

    return freq;
  }



  public static void main (String [] args) throws IOException {
    final String inputFilelist = args[0];
    //final String outputFile = args[1];
    final String locationFile1 = args[1];
    final String locationFile2 = args[2];
    final String keywordFile = args[3];
    final String option = args[4];        // 1 || 2

    // we want to detect cross border movement between the following two sets of locations
    final ImmutableSet<String> locations1 = ImmutableSet.copyOf(Files.asCharSource(new File(locationFile1), Charsets.UTF_8).readLines());
    final ImmutableSet<String> locations2 = ImmutableSet.copyOf(Files.asCharSource(new File(locationFile2), Charsets.UTF_8).readLines());
    final ImmutableSet<String> keywords = ImmutableSet.copyOf(Files.asCharSource(new File(keywordFile), Charsets.UTF_8).readLines());

    final ImmutableList<String> listStringFiles = Files.asCharSource(new File(inputFilelist), Charsets.UTF_8).readLines();

    List<File> filesToProcess = new ArrayList<File>();
    for(String strFile : listStringFiles)
      filesToProcess.add(new File(strFile));

    SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().build();

    for (final DocTheory dt : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
      final String docid = dt.docid().toString();
      final String docYear = docid.substring(7, 11);

      final ImmutableMultiset<String> extractedKeywords = extractKeywords(dt, keywords, true);
      final int numberOfUniqueKeywords = extractedKeywords.elementSet().size();
      final int keywordsFrequency = extractedKeywords.size();

      final ImmutableMultiset<String> extractedLocations1 = extractKeywords(dt, locations1, false);
      //final ImmutableMultiset<String> extractedLocations2 = extractKeywords(dt, locations2, false);

      final ImmutableMultiset<String> extractedSS = extractKeywords(dt, ImmutableSet.copyOf(
          Arrays.asList("South Sudan", "South Sudanese")), false);
      final ImmutableMultiset<String> extractedEth = extractKeywords(dt, ImmutableSet.of("Ethiopia"), false);

      //if(extractedSS.size()>0 && extractedEth.size()>0) {
      if((option.equals("1") && extractedSS.size()>=1) || (option.equals("2") && extractedLocations1.elementSet().size()>=1) && extractedEth.size()>=1) {
        if(numberOfUniqueKeywords >= 1) {

          StringBuffer s = new StringBuffer();
          for(final String w : extractedKeywords.elementSet()) {
            s.append(" ");
            s.append(w);
          }

          //if(extractedLocations1.elementSet().size()>=3 && extractedLocations2.elementSet().size()>=3) {
          System.out.println(docYear + "\t" + docid + "\t" + keywordsFrequency + "\t" + s.toString());
          //}
        }

      }
    }


    /*
    int hasBothLocationsCount = 0;
    int hasMovementEventCount = 0;
    int hasMigrationEventCount = 0;

    Multiset<String> hasBothLocationYear = HashMultiset.create();
    Multiset<String> hasMovementEventYear = HashMultiset.create();
    Multiset<String> hasMigrationEventYear = HashMultiset.create();

    //Multiset<String> eventAnchors = HashMultiset.create();
    int docIndex = 0;
    for (final DocTheory dt : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
      for(int i=0; i<dt.numSentences(); i++) {
        if(dt.sentenceTheory(i).isEmpty()) {
          continue;
        }
        final String docid = dt.docid().toString();
        final String docYear = docid.substring(7, 11);

        String sentenceText = dt.sentenceTheory(i).span().text().utf16CodeUnits().toString();
        sentenceText = " " + sentenceText + " ";

        boolean foundLocation1 = false;
        boolean foundLocation2 = false;
        for(int j=0; j<locations1.size(); j++) {
          if(sentenceText.indexOf(locations1.get(j))!=-1) {
            foundLocation1 = true;
          }
        }
        for(int j=0; j<locations2.size(); j++) {
          if(sentenceText.indexOf(locations2.get(j))!=-1) {
            foundLocation2 = true;
          }
        }
        if(foundLocation1 == true && foundLocation2 == true) {
          hasBothLocationsCount += 1;
          hasBothLocationYear.add(docYear);
        } else {
          continue;
        }

        for(final EventMention em : dt.sentenceTheory(i).eventMentions()) {
          final String eventType = em.type().asString();
          //final String anchorText = em.anchorNode().span().text().toString().toLowerCase().replaceAll("\t'", "_").replaceAll(" ", "_");

          //final SynNode anchorHead = em.anchorNode().head();
          //final String headPOS = anchorHead.headPOS().asString();
          //final String headText = anchorHead.tokenSpan().originalText().content().utf16CodeUnits().toLowerCase().replaceAll(" ", "_");

          //writer.write("\n\nEVENT: " + eventType + "\t" + headText);
          //writer.write("\n - " + sentenceText);

          //for(final EventMention.Argument arg : em.arguments()) {
          //  final String role = arg.role().asString();
          //  final String argText = arg.span().text().utf16CodeUnits().toString();
          //  writer.write("\n - " + role + "\t" + argText);
          //}

          if(eventType.compareTo("Movement")==0 || eventType.compareTo("Migration")==0 || eventType.compareTo("HumanDisplacement")==0) {
            hasMovementEventCount += 1;
            hasMovementEventYear.add(docYear);
            if(eventType.compareTo("Migration")==0 || eventType.compareTo("HumanDisplacement")==0) {
              hasMigrationEventCount += 1;
              hasMigrationEventYear.add(docYear);
            }
          }
        }
      }

      docIndex += 1;
      if((docIndex % 100)==0) {
        System.out.println("Processed " + docIndex + " documents");
      }
    }

    //writer.close();


    System.out.println("hasBothLocationsCount=" + hasBothLocationsCount + ", hasMovementEventCount=" + hasMovementEventCount + " hasMigrationEventCount=" + hasMigrationEventCount);
    System.out.println("#### hasBothLocationYear");
    List<String> bothLocationYears = Lists.newArrayList(hasBothLocationYear.elementSet());
    Collections.sort(bothLocationYears);
    //for(final String docYear : Collections.sort(Lists.newArrayList(hasBothLocationYear.elementSet()))) {
    //for(final String docYear : hasBothLocationYear.elementSet()) {
    for(final String docYear : bothLocationYears) {
      System.out.println(docYear + " " + hasBothLocationYear.count(docYear));
    }

    System.out.println("#### hasMovementEventYear");
    List<String> movementEventYears = Lists.newArrayList(hasMovementEventYear.elementSet());
    Collections.sort(movementEventYears);
    //for(final String docYear : Collections.sort(Lists.newArrayList(hasMovementEventYear.elementSet()))) {
    for(final String docYear : movementEventYears) {
      System.out.println(docYear + " " + hasMovementEventYear.count(docYear));
    }

    System.out.println("#### hasMigrationEventYear");
    List<String> migrationEventYears = Lists.newArrayList(hasMigrationEventYear.elementSet());
    Collections.sort(migrationEventYears);
    //for(final String docYear : Collections.sort(Lists.newArrayList(hasMigrationEventYear.elementSet()))) {
    for(final String docYear : migrationEventYears) {
      System.out.println(docYear + " " + hasMigrationEventYear.count(docYear));
    }
    */

  }


}




