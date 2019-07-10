package com.bbn.necd.event.sandbox;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.SentenceInformation;
import com.bbn.necd.event.features.BackgroundInformation;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventFeaturesUtils;
import com.bbn.nlp.WordAndPOS;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;

/**
 * Created by ychan on 5/4/16.
 */
public final class TryDocumentInfo {
  private static final Logger log = LoggerFactory.getLogger(TryDocumentInfo.class);

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

    final ImmutableMap<Symbol, EventFeatures> eventFeatures =
        EventFeaturesUtils.readEventFeatures(params.getExistingFile("eventFeatures"));

    for(final EventFeatures eg : eventFeatures.values()) {
      final Symbol docId = eg.docId();
      final int sentenceIndex = eg.sentenceIndex();

      final SentenceInformation
          sentenceInformation = backgroundInfo.getDocSentences().get(docId, sentenceIndex);

      final ImmutableList<Symbol> predicates = eg.predicates();
      final ImmutableList<Integer> predicateTokenIndices = eg.predicateTokenIndices();

      assert(predicates.size() == predicateTokenIndices.size());

      for(int i=0; i<predicates.size(); i++) {
        final Symbol predicate = predicates.get(i);
        final int tokenIndex = predicateTokenIndices.get(i);

        final WordAndPOS wordAndPOS = sentenceInformation.wordAndPOS().get(tokenIndex);
        final Symbol word = wordAndPOS.word();

        //log.info("{} {} {}", tokenIndex, predicate.asString(), word.asString());
        assert(predicate.asString().equals(word.asString()));
      }

    }

  }
}
