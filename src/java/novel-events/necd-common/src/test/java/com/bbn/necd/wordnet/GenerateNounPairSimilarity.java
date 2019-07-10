package com.bbn.necd.wordnet;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.nlp.banks.wordnet.WordNet;
import com.bbn.nlp.banks.wordnet.WordNetPOS;
import com.google.common.base.Charsets;
import com.google.common.base.Joiner;
import com.google.common.base.Optional;
import com.google.common.io.CharSink;
import com.google.common.io.CharSource;
import com.google.common.io.Files;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.util.List;

/**
 * Generate noun pair similarity measures.
 */
public final class GenerateNounPairSimilarity {

  private static final Logger logger = LoggerFactory.getLogger(GenerateNounPairSimilarity.class);

  public static void main(String[] args) throws IOException {
    if (args.length != 2) {
      System.err.println("Usage: GenerateNounPairSimilarity wordfile outputfile");
      System.exit(1);
    }

    // Load params from resource
    final File wordNetParams = new File(GenerateNounPairSimilarity.class.getResource("/wordnet.params").getFile());

    final String inputPath = args[0];
    final String outputPath = args[1];
    logger.info("Reading from '{}', writing to '{}'", inputPath, outputPath);

    // Open input and output
    final CharSource input = Files.asCharSource(new File(inputPath), Charsets.UTF_8);
    final CharSink output = Files.asCharSink(new File(outputPath), Charsets.UTF_8);
    final BufferedWriter writer = new BufferedWriter(output.openBufferedStream());

    // Get words
    final List<String> words = input.readLines();

    // Load up wordnet
    logger.info("Loading WordNet");
    final WordNet wordNet = WordNet.fromParameters(Parameters.loadSerifStyle(wordNetParams));
    logger.info("Loading WordNet similarity");
    final WordNetSimilarity sim = WordNetSimilarity.fromWordNet(wordNet, WordNetPOS.NOUN);

    // Other setup
    final Joiner tabJoiner = Joiner.on("\t");
    final String feature = "WordNet:wupsim";

    logger.info("Writing output features");
    // The minimum similarity for Wu and Palmer Consim assumes that the subsumer node is just below root and the
    // two stems are maximal distance from that node. (c1 = c2 = height, c3 = 1)
    final double minSimilarity = sim.wuPalmerMinConSim();
    for (String word1 : words) {
      for (String word2 : words) {
        // Skip if it's the same word
        if (word1.equals(word2)) {
          continue;
        }
        Optional<Double> similarity = sim.wuPalmerConSim(Symbol.from(word1), Symbol.from(word2));
        double distance = similarity.isPresent()
            ? similarity.get()
            : minSimilarity;
        writer.write(tabJoiner.join(word1 + "/N", feature, word2 + "/N", distance));
        writer.newLine();
      }
    }
    writer.close();
  }
}
