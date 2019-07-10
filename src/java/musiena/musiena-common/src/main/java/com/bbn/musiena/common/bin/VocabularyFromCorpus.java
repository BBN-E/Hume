package com.bbn.musiena.common.bin;

import com.bbn.bue.common.parameters.Parameters;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultiset;
import com.google.common.collect.Multiset;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.util.Map;

public final class VocabularyFromCorpus {
  private static final Logger log = LoggerFactory.getLogger(VocabularyFromCorpus.class);

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

    final int frequencyThreshold = params.getInteger("frequencyThreshold");
    final int alphabetCountThreshold = params.getInteger("alphabetCountThreshold");

    final ImmutableMap<String, Integer> vocab = filterVocabulary(constructVocabularyFromCorpus(params.getExistingFile("corpus")), frequencyThreshold, alphabetCountThreshold);

    writeVocabToFile(vocab, params.getCreatableFile("vocab"));
  }

  private static ImmutableMultiset<String> constructVocabularyFromCorpus(final File corpus) throws IOException {
    final ImmutableMultiset.Builder<String> ret = ImmutableMultiset.builder();

    log.info("Construct initial vocabulary");

    final BufferedReader reader = Files.asCharSource(corpus, Charsets.UTF_8).openBufferedStream();

    int lineCount = 0;

    String line = "";
    while((line = reader.readLine())!=null) {
      final String[] tokens = line.split(" ");
      for(int i=0; i<tokens.length; i++) {
        ret.add(tokens[i]);
      }

      lineCount += 1;
      if((lineCount % 100000)==0) {
        log.info("{} line read", lineCount);
      }
    }

    reader.close();

    return ret.build();
  }

  private static ImmutableMap<String, Integer> filterVocabulary(final ImmutableMultiset<String> vocab, final int freqThreshold, final int alphabetCountThreshold) {
    final ImmutableMap.Builder<String, Integer> ret = ImmutableMap.builder();

    log.info("Filtering vocabulary");

    for(final Multiset.Entry<String> v : vocab.entrySet()) {
      final String w = v.getElement();
      final int c = v.getCount();

      if(c >= freqThreshold) {
        int alphabetCount = 0;
        for(int i=0; i<w.length(); i++) {
          if(w.charAt(i) >= 'a' && w.charAt(i) <= 'z') {
            alphabetCount += 1;
          }
        }

        if(alphabetCount >= alphabetCountThreshold) {
          ret.put(w, c);
        }
      }
    }

    return ret.build();
  }

  private static void writeVocabToFile(final ImmutableMap<String, Integer> vocab, final File outfile) throws IOException {
    final Writer writer = Files.asCharSink(outfile, Charsets.UTF_8).openBufferedStream();

    log.info("Writing out vocabulary");

    //final Comparator valueComparator = Ordering.natural().onResultOf(Functions.forMap(vocab));
    //final ImmutableMap<String, Integer> sortedMap = ImmutableSortedMap.copyOf(vocab, valueComparator);

    for(final Map.Entry<String, Integer> entry : vocab.entrySet()) {
      writer.write(entry.getKey() + " " + entry.getValue() + "\n");
    }

    writer.close();
  }
}
