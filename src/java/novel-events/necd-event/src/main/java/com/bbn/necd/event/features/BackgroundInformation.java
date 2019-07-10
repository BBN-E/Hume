package com.bbn.necd.event.features;


import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.parameters.ParametersModule;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.theory.DocumentInformation;
import com.bbn.necd.common.theory.SentenceInformation;
import com.bbn.necd.event.io.CompressedFileUtils;
import com.bbn.nlp.banks.wordnet.IWordNet;
import com.bbn.nlp.banks.wordnet.WordNetM;
import com.bbn.nlp.banks.wordnet.WordNetPOS;
import com.bbn.nlp.languages.English;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Sets;
import com.google.common.io.Files;
import com.google.inject.Guice;

import org.apache.commons.io.Charsets;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Set;

/*
  This could store several backend information, e.g. the embeddings, sentence tokens, etc.

  Parameters:
  - docInfoDirectory

  - * from PredictVectorManager
      - data.predictVectorFile
      - feature.minValue
 */
public final class BackgroundInformation {
  private static final Logger log = LoggerFactory.getLogger(BackgroundInformation.class);

  private final PredictVectorManager predictVectorManager;
  private final ImmutableTable<Symbol, Integer, SentenceInformation> docSentences;
  private final ImmutableSet<Symbol> eventWords;
  private final English language;
  private final IWordNet wordNet;

  private BackgroundInformation(final PredictVectorManager predictVectorManager,
      final ImmutableTable<Symbol, Integer, SentenceInformation> docSentences,
      final ImmutableSet<Symbol> eventWords, final English language, final IWordNet wordNet) {
    this.predictVectorManager = predictVectorManager;
    this.docSentences = docSentences;
    this.eventWords = eventWords;
    this.language = language;
    this.wordNet = wordNet;
  }

  public PredictVectorManager getPredictVectorManager() {
    return predictVectorManager;
  }

  public ImmutableTable<Symbol, Integer, SentenceInformation> getDocSentences() {
    return docSentences;
  }

  public ImmutableSet<Symbol> getEventWords() {
    return eventWords;
  }

  public English getLanguage() {
    return language;
  }

  public IWordNet getWordNet() {
    return wordNet;
  }

  public static BackgroundInformation fromParams(final Parameters params) throws IOException {
    log.info("Loading predict vectors");
    final PredictVectorManager predictVectorManager = PredictVectorManager.fromParams(params).build();
    final ImmutableTable<Symbol, Integer, SentenceInformation> docSentences =
        loadDocSentenceInfo(params.getExistingDirectory("docInfoDirectory"), params.getOptionalBoolean("docInfo.load"));
    log.info("Done loading document information");

    //final ImmutableSet<Symbol> eventWords = readWordList(params.getExistingFile("eventWords"));
    final ImmutableSet<Symbol> eventWords = ImmutableSet.of();

    final English language = English.getInstance();

    final File wordNetParamsFile = params.getExistingFile("com.bbn.necd.event.features.wordNetParams").getAbsoluteFile();
    final Parameters wordNetParams = Parameters.loadSerifStyle(wordNetParamsFile);
    final ParametersModule paramsModule = ParametersModule.createAndDump(wordNetParams);
    final IWordNet wordNet = Guice.createInjector(
        paramsModule, WordNetM.fromParameters(wordNetParams)).getInstance(IWordNet.class);

    //final WordNet wordNet = WordNet.fromParameters(params);

    return new BackgroundInformation(predictVectorManager, docSentences, eventWords, language, wordNet);
  }

  private static ImmutableSet<Symbol> readWordList(final File wordFile) throws IOException {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    final ImmutableList<String> lines = Files.asCharSource(wordFile, Charsets.UTF_8).readLines();

    for(final String line : lines) {
      ret.add(Symbol.from(line));
    }

    return ret.build();
  }

  private static ImmutableTable<Symbol, Integer, SentenceInformation> loadDocSentenceInfo(
      final File docInfoDir, final Optional<Boolean> docInfoLoad) throws IOException {
    final ImmutableTable.Builder<Symbol, Integer, SentenceInformation> ret =
        ImmutableTable.builder();

    if(docInfoLoad.isPresent() && docInfoLoad.get()) {
      for (final File file : FileUtils
          .listFiles(docInfoDir, new String[]{"docInfo.json.gz"}, false)) {
        if(file.getName().startsWith("20")) {
          log.info("loading from {}", file.getName());
          final ImmutableList<DocumentInformation>
              docs = CompressedFileUtils.readAsJsonList(file, DocumentInformation.class);

          for (final DocumentInformation doc : docs) {
            final Symbol docId = doc.docId();

            for (final SentenceInformation sent : doc.sentencesInformation()) {
              ret.put(docId, sent.sentenceNum(), sent);
            }

          }
        }
      }
    }

    return ret.build();
  }

  public boolean isAuxiliaryVerb(final Symbol w) {
    return auxiliaryVerbs.contains(Symbol.from(w.asString().toLowerCase()));
  }

  public boolean isPronounPOS(final Symbol postag) {
    return pronounPOS.contains(postag);
  }

  public Symbol toLemma(final Symbol w, final Symbol pos) {
    final Optional<WordNetPOS> wnPos = wordNet.language().wordnetPOS(pos);
    if(wnPos.isPresent() && w.asString().indexOf("_")==-1) {
      final Optional<Symbol> stem = wordNet.getFirstStem(w, wnPos.get());
      if(stem.isPresent()) {
        return stem.get();
      } else {
        return w;
      }
    } else {
      return w;
    }
  }

  // Ideally this should go in a resource list to be loaded. But since it is just a small fixed set, I'll keep it simple.
  private final static Set<Symbol> auxiliaryVerbs =  Sets.newHashSet(
      Symbol.from("be"),Symbol.from("am"),
      Symbol.from("are"),Symbol.from("is"),Symbol.from("was"),Symbol.from("were"),
      Symbol.from("being"),Symbol.from("been"),
      Symbol.from("can"),Symbol.from("could"),
      Symbol.from("do"),Symbol.from("did"),Symbol.from("does"),Symbol.from("doing"),
      Symbol.from("have"),Symbol.from("had"),Symbol.from("has"),Symbol.from("having"),
      Symbol.from("may"),Symbol.from("might"),Symbol.from("must"),
      Symbol.from("shall"),Symbol.from("should"),Symbol.from("will"),Symbol.from("would"));

  private final static Set<Symbol> pronounPOS = Sets.newHashSet(
      Symbol.from("PRP"), Symbol.from("PRP$"), Symbol.from("WP"), Symbol.from("WP$"));

}

