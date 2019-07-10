package com.bbn.causeex.event.bin;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.causeex.common.CollectionUtils;
import com.bbn.causeex.common.Lemmatizer;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Parse;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMultiset;
import com.google.common.collect.Maps;
import com.google.common.collect.Multiset;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.util.Map;


public final class GenericTriggerCounter {

  private static final Logger log = LoggerFactory.getLogger(GenericTriggerCounter.class);

  public static void main(final String[] argv) throws IOException {
    try {
      trueMain(argv[0]);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(1);
    }
  }

  private static void trueMain(final String paramFile) throws IOException {
    final Parameters params = Parameters.loadSerifStyle(new File(paramFile));
    log.info(params.dump());

    final Lemmatizer lemmatizer = Lemmatizer.from("lemma.nv");

    final ImmutableList<File> serifxmls = FileUtils
        .loadFileList(
            Files.asCharSource(params.getExistingFile("serifxml.filelist"), Charsets.UTF_8));

    final int freqThreshold = params.getInteger("freqThreshold");

    final ImmutableMultiset<String> vocab = genericTriggersFromSerifXmls(serifxmls, lemmatizer, params.getString("output_dir"));

    sortAndWriteToFile(vocab, params.getCreatableFile("counts.output"), freqThreshold);
  }

  private static void sortAndWriteToFile(final ImmutableMultiset<String> vocab, final File outfile, final int freqThreshold) throws IOException {
    Map<String, Integer> counts = Maps.newHashMap();
    for (final Multiset.Entry<String> entry : vocab.entrySet()) {
      if (entry.getCount() >= freqThreshold) {
        counts.put(entry.getElement(), entry.getCount());
      }
    }

    final Writer writer = Files.asCharSink(outfile, Charsets.UTF_8)
        .openBufferedStream();
    for (final Map.Entry<String, Integer> entry : CollectionUtils.entryIntegerValueOrdering
        .immutableSortedCopy(counts.entrySet())) {
      writer.write(entry.getKey() + " " + entry.getValue() + "\n");
    }
    writer.close();
  }

  private static ImmutableMultiset<String> genericTriggersFromSerifXmls(
      final ImmutableList<File> serifxmls, final Lemmatizer lemmatizer, final String outputDir) throws IOException {
    final SerifXMLLoader serifXMLLoader =
        SerifXMLLoader.builderFromStandardACETypes().allowSloppyOffsets().makeAllTypesDynamic()
            .build();

    final ImmutableMultiset.Builder<String> multiSetBuilder = ImmutableMultiset.builder();
    int fileCounter = 0;
    for (final File file : serifxmls) {
      final ImmutableMultiset.Builder<String> docVocabBuilder = ImmutableMultiset.builder();

      final DocTheory dt = serifXMLLoader.loadFrom(file);

      for (final SentenceTheory st : dt.nonEmptySentenceTheories()) {
        final Parse parse = st.parse().get();
        final SynNode root = parse.root();
        for (int i = 0; i < root.numTerminals(); i++) {
          final SynNode node = root.nthTerminal(i);

          final String posTag = node.headPOS().asString();
          final String text = node.headWord().asString();

          if (posTag.startsWith("VB")) {
            final String lemma = lemmatizer.getLemma(text);
            multiSetBuilder.add(lemma + ".v");
            docVocabBuilder.add(lemma + ".v");
          } else if (posTag.compareTo("NN") == 0 || posTag.compareTo("NNS") == 0) {
            final String lemma = lemmatizer.getLemma(text);
            multiSetBuilder.add(lemma + ".n");
            docVocabBuilder.add(lemma + ".n");
          }
        }
      }

      final String filename = file.getName();
      final String docid = filename.substring(0, filename.lastIndexOf('.'));

      final ImmutableMultiset<String> docVocab = docVocabBuilder.build();
      sortAndWriteToFile(docVocab, new File(outputDir+ "/" + docid), 1);

      fileCounter += 1;
      if((fileCounter % 100)==0) {
        System.out.println("Processed " + fileCounter + " documents");
      }
    }

    return multiSetBuilder.build();
  }

  /*
  public static ImmutableMap<String, String> readLemmatizationDictionary(final File infile) throws IOException {
    final ImmutableMap.Builder<String, String> ret = ImmutableMap.builder();

    final Splitter spaceSplitter = Splitter.on(" ");

    for(final String line : Files.asCharSource(infile, Charsets.UTF_8).readLines()) {
      final ImmutableList<String> tokens = ImmutableList.copyOf(spaceSplitter.split(line));
      ret.put(tokens.get(0), tokens.get(1));
    }

    return ret.build();
  }
  */
}
