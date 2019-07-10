package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.theory.DocumentInformation;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.common.theory.SentenceInformation;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventFeaturesUtils;
import com.bbn.necd.event.io.CompressedFileUtils;
import com.bbn.nlp.WordAndPOS;
import com.bbn.nlp.languages.English;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableMultiset;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Maps;

import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Collection;
import java.util.Map;

/**
 * Created by ychan on 4/11/16.
 */
public final class ExploreAverageEmbeddings {
  private static final Logger log = LoggerFactory.getLogger(ExploreAverageEmbeddings.class);

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



    // load the examples
    final ImmutableMap<Symbol, EventFeatures> eventFeatures = EventFeaturesUtils.readEventFeatures(params.getExistingFile("eventFeatures"));

    // we are only concerned with the set of documents that these examples are extracted from
    final ImmutableSet<Symbol> targetDocIds = getDocIds(eventFeatures.values());

    // load the sentences for above target set of documents
    final ImmutableTable<Symbol, Integer, SentenceInformation> docSentences = loadDocSentenceInfo(params.getExistingDirectory("docInfoDirectory"), targetDocIds);

    log.info("loading PredictVectorManager");
    final PredictVectorManager predictVectorManager = PredictVectorManager.fromParams(params).build();
    log.info("loaded PredictVectorManager");

    final English lang = English.getInstance();

    int counter = 0;
    Map<Symbol, RealVector> wordToPVCache = Maps.newHashMap();
    for(final EventFeatures example : eventFeatures.values()) {
      final ImmutableMultiset<Symbol> sw = getSurroundingWords(example, docSentences, lang);

      final ImmutableSet.Builder<RealVector> embeddingsBuilder = ImmutableSet.builder();
      for(final Symbol w : sw.elementSet()) {
        final int frequency = sw.count(w);
        Optional<RealVector> wordEmbedding = Optional.absent();

        if(wordToPVCache.containsKey(w)) {
          wordEmbedding = Optional.of(wordToPVCache.get(w));
        } else {
          final Optional<PredictVectorManager.PredictVector> pv = predictVectorManager.getVector(w);
          if (pv.isPresent()) {
            final RealVector rv = RealVector.toRealVector(pv.get().getValues());
            wordToPVCache.put(w, rv);
            wordEmbedding = Optional.of(rv);
          }
        }

        if(wordEmbedding.isPresent()) {
          embeddingsBuilder.add(wordEmbedding.get());
        }
      }
      final ImmutableSet<RealVector> embeddings = embeddingsBuilder.build();

      //log.info("Event example {} has embeddings based on {} words", example.id(), embeddings.size());

      // this is the average embeddings based on surrounding words
      final RealVector avgEmbedding = average(embeddings);

      counter += 1;
      if((counter % 1000)==0) {
        log.info("Examined {} examples", counter);
      }
    }
  }


  public static RealVector average(final ImmutableCollection<RealVector> vectors) {
    final ImmutableMultimap.Builder<Integer, Double> aggregateValuesBuilder = ImmutableMultimap.builder();
    for(final RealVector v : vectors) {
      for(final Map.Entry<Integer, Double> entry : v.getElements().entrySet()) {
        aggregateValuesBuilder.put(entry.getKey(), entry.getValue());
      }
    }
    final ImmutableMultimap<Integer, Double> aggregateValues = aggregateValuesBuilder.build();

    final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();
    for(final Map.Entry<Integer, Collection<Double>> entry : aggregateValues.asMap().entrySet()) {
      final Integer key = entry.getKey();
      double valueSum = 0;
      for(final Double value : entry.getValue()) {
        valueSum += value;
      }
      ret.put(key, valueSum/vectors.size());
    }

    return RealVector.builder(false).withElements(ret.build()).build();
  }

  public static ImmutableMultiset<Symbol> getSurroundingWords(final EventFeatures example, final ImmutableTable<Symbol, Integer, SentenceInformation> docSentences, final English lang) {
    final ImmutableMultiset.Builder<Symbol> ret = ImmutableMultiset.builder();

    final Symbol docId = example.docId();
    final int sentenceIndex = example.sentenceIndex();

    for(int index=(sentenceIndex-sentenceWindowSize); index<=(sentenceIndex+sentenceWindowSize); index++) {
      if(docSentences.contains(docId, index)) {
        final SentenceInformation sentInfo = docSentences.get(docId, index);
        ret.addAll(getEventiveVerbs(sentInfo, lang));
        ret.addAll(getEventiveNouns(sentInfo, lang));
      }
    }

    return ret.build();
  }


  // there are many ways to define what is an eventive verb. For the moment, we exclude modals, and exclude corpulas
  public static ImmutableList<Symbol> getEventiveVerbs(final SentenceInformation sentence, final English lang) {
    final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();

    for(final WordAndPOS wordPos : sentence.wordAndPOS()) {
      final Symbol word = wordPos.word();
      final Symbol POS = wordPos.POS();
      if(lang.isVerbalPOSExcludingModals(POS) && !lang.wordIsCopula(word)) {
        ret.add(word);
      }
    }

    return ret.build();
  }

  // ideally, we want to pre-generate a list of deverbal nouns
  public static ImmutableList<Symbol> getEventiveNouns(final SentenceInformation sentence, final English lang) {
    final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();

    for(final WordAndPOS wordPos : sentence.wordAndPOS()) {
      final Symbol word = wordPos.word();
      final Symbol POS = wordPos.POS();

      if(POS.equalTo(NN) || POS.equalTo(NNS)) {
        ret.add(word);
      }
    }

    return ret.build();
  }


  private static ImmutableTable<Symbol, Integer, SentenceInformation> loadDocSentenceInfo(final File docInfoDir, final ImmutableSet<Symbol> targetDocIds) throws  IOException {
    final ImmutableTable.Builder<Symbol, Integer, SentenceInformation> ret = ImmutableTable.builder();

    for(final File file : FileUtils.listFiles(docInfoDir, new String[]{"docInfo.json.gz"}, false)) {
      log.info("loading from {}", file.getName());
      final ImmutableList<DocumentInformation> docs = CompressedFileUtils.readAsJsonList(file, DocumentInformation.class);

      for(final DocumentInformation doc : docs) {
        final Symbol docId = doc.docId();

        if(targetDocIds.contains(docId)) {
          for (final SentenceInformation sent : doc.sentencesInformation()) {
            ret.put(docId, sent.sentenceNum(), sent);
          }
        }
      }
    }

    return ret.build();
  }

  private static ImmutableSet<Symbol> getDocIds(final ImmutableCollection<EventFeatures> examples) {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    for(final EventFeatures eg : examples) {
      ret.add(eg.docId());
    }

    return ret.build();
  }

  /*
  private static ImmutableMultimap<Symbol, Integer> getTargetSentenceIndices(final File eventFeaturesFile) throws IOException {
    final ImmutableMultimap.Builder<Symbol, Integer> ret = ImmutableMultimap.builder();

    final ImmutableMap<Symbol, EventFeatures> eventFeatures = EventFeaturesUtils.readEventFeatures(eventFeaturesFile);
    for(final EventFeatures eg : eventFeatures.values()) {
      final Symbol docId = eg.docId();
      final int sentenceIndex = eg.sentenceIndex();

      ret.put(docId, sentenceIndex);
    }

    return ret.build();
  }
  */

  private final static Symbol NN = Symbol.from("NN");
  private final static Symbol NNS = Symbol.from("NNS");

  private final static int sentenceWindowSize = 1;
}
