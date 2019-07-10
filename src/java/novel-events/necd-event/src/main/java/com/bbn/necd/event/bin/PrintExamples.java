package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.SentenceInformation;
import com.bbn.necd.event.features.BackgroundInformation;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventFeaturesUtils;
import com.bbn.nlp.WordAndPOS;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;
import com.google.common.io.Files;
import com.google.common.primitives.Doubles;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 7/19/16.
 */
public final class PrintExamples {

  private static final Logger log = LoggerFactory.getLogger(DoTraining.class);

  public static void main(String[] argv) {
    // we wrap the main method in this way to
    // ensure a non-zero return value on failure
    try {
      trueMain(argv);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(1);
    }
  }

  public static void trueMain(final String[] argv) throws IOException, ClassNotFoundException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final BackgroundInformation backgroundInfo = BackgroundInformation.fromParams(params);

    final ImmutableSet<Symbol> ids = readIds(params.getExistingFile("ids"));

    final ImmutableMap<Symbol, EventFeatures> examples = readEventFeatures(params.getExistingFile("eventFeaturesFilelist"));

    final ImmutableMap<String, Double> enePredictions = readEnePredictions(params);

    for(final Symbol id : ids) {
      final EventFeatures eg = examples.get(id);

      final double eneScore = enePredictions.get(id.asString());

      System.out.println(eg.id().asString());
      System.out.println(eneScore);

      final Symbol docId = eg.docId();
      final int sentenceIndex = eg.sentenceIndex();
      System.out.println(printSentence(backgroundInfo.getDocSentences().get(docId, sentenceIndex)));

      System.out.println("SOURCE: " + StringUtils.join(toStrings(eg.sourceTokens()), " "));
      //System.out.println("SOURCE-SEC: " + StringUtils.join(toStrings(eg.sourceSectors()), "|"));
      //System.out.println("SOURCE-SECHEAD: " + StringUtils.join(toSectorHeads(eg.sourceSectors()), "|"));
      System.out.println("PREDICATES: " + StringUtils.join(toStrings(eg.predicates()), " "));
      System.out.println("TARGET: " + StringUtils.join(toStrings(eg.targetTokens()), " "));
      //System.out.println("TARGET-SEC: " + StringUtils.join(toStrings(eg.targetSectors()), "|"));
      //System.out.println("TARGET-SECHEAD: " + StringUtils.join(toSectorHeads(eg.targetSectors()), "|"));
      System.out.println("");
    }

    /*
    final ImmutableMap<Symbol, PropositionTreeEvent> events = EventUtils.loadProcessedEvents(ids, params.getExistingFile("events"), false);
    log.info("Read {} events", events.keySet().size());

    for(final PropositionTreeEvent eg : events.values()) {

      System.out.println(eg.getId().asString());

      final Symbol docId = eg.getDocId();
      final int sentenceIndex = eg.getSentenceIndex();

      System.out.println(printSentence(backgroundInfo.getDocSentences().get(docId, sentenceIndex)));

      System.out.println("SOURCE: " + StringUtils.join(toStrings(eg.getSourceTokens()), " "));

      System.out.println("PREDICATES: " + StringUtils.join(toStrings(eg.getPredicates()), " "));
      System.out.println("TARGET: " + StringUtils.join(toStrings(eg.getTargetTokens()), " "));

      System.out.println("");
    }
    */
  }

  private static ImmutableMap<String, Double> readEnePredictions(final Parameters params) throws IOException {
    final ImmutableMap.Builder<String, Double> ret = ImmutableMap.builder();

    final ImmutableList<String> predictionLines = Files.asCharSource(params.getExistingFile("ene.predictions"), Charsets.UTF_8).readLines();

    int counter = 1;
    for(final String line : Files.asCharSource(params.getExistingFile("ene.sparseVector.log"), Charsets.UTF_8).readLines()) {

      final String[] tokens = StringUtils.split(line, " ");
      final String id = tokens[0];

      final String[] pTokens = predictionLines.get(counter).split(" ");
      ret.put(id, Doubles.tryParse(pTokens[1]).doubleValue());

      counter += 1;
    }

    return ret.build();
  }

  private static ImmutableSet<String> toSectorHeads(final ImmutableList<Symbol> sectors) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    for(final Symbol sector : sectors) {
      final String sectorString = sector.asString();

      if(sectorString.indexOf("/")!=-1) {
        final String[] sectorTokens = sectorString.split("/");
        for(final String sectorToken : sectorTokens) {
          final String[] tokens = StringUtils.split(StringUtils.removeEnd(StringUtils.removeStart(sectorToken, " "), " "), " ");
          ret.add(tokens[tokens.length-1]);
        }
      } else {
        final String[] tokens = StringUtils.split(sectorString, " ");
        ret.add(tokens[tokens.length-1]);
      }
    }

    return ret.build();
  }


  private static ImmutableSet<Symbol> readIds(final File file) throws IOException {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    for(final String line : Files.asCharSource(file, Charsets.UTF_8).readLines()) {
      ret.add(Symbol.from(line));
    }

    return ret.build();
  }

  private static ImmutableList<String> toStrings(final List<Symbol> tokens) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    for(final Symbol token : tokens) {
      ret.add(token.asString());
    }

    return ret.build();
  }

  private static String printSentence(final SentenceInformation sent) {
    List<Symbol> words = Lists.newArrayList();
    for(final WordAndPOS wp : sent.wordAndPOS()) {
      words.add(wp.word());
    }

    return StringUtils.join(toStrings(words), " ");
  }

  private static ImmutableMap<Symbol, EventFeatures> readEventFeatures(final File filelist) throws IOException {
    final ImmutableMap.Builder<Symbol, EventFeatures> ret = ImmutableMap.builder();
    Set<Symbol> seenIds = Sets.newHashSet();

    for(final String filename : Files.asCharSource(filelist, Charsets.UTF_8).readLines()) {
      final ImmutableMap<Symbol, EventFeatures> eventFeatures = EventFeaturesUtils.readEventFeatures(new File(filename));
      for(final Map.Entry<Symbol, EventFeatures> entry : eventFeatures.entrySet()) {
        final Symbol id = entry.getKey();
        final EventFeatures eg = entry.getValue();
        if(!seenIds.contains(id)) {
          ret.put(entry);
          seenIds.add(id);
        }
      }
    }

    return ret.build();
  }
}
