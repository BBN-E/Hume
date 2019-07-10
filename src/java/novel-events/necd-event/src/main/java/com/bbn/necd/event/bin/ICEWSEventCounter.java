package com.bbn.necd.event.bin;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.io.GZIPByteSource;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.icews.CAMEOCodes;
import com.bbn.necd.event.io.DelimUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMentions;
import com.google.common.base.Charsets;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.Multiset;
import com.google.common.collect.Multisets;
import com.google.common.io.CharSink;
import com.google.common.io.Files;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.util.List;

/**
 * Output counts for top-level ICEWS event codes to a csv file.
 */
public final class ICEWSEventCounter {

  private static final Logger log = LoggerFactory.getLogger(ICEWSEventCounter.class);

  public static void main(final String[] args) throws IOException {
    // Parse arguments
    if (args.length != 1) {
      System.err.println("Usage: icewsEventCounter params");
      System.exit(1);
    }
    final Parameters params = Parameters.loadSerifStyle(new File(args[0]));
    final Parameters eventParams = params.copyNamespace("com.bbn.necd.event.extractor");
    final List<File> inputFiles = FileUtils.loadFileList(eventParams.getExistingFile("serifXmlFileList"));
    final File outputDir = eventParams.getAndMakeDirectory("extractedEventsCounts");

    log.info("Reading files from {}", args[0]);
    final File outputFile = new File(outputDir, "accent_codes.csv");
    log.info("Writing counts to {}", outputFile);
    final CharSink outputSink = Files.asCharSink(outputFile, Charsets.UTF_8);

    // Initialize counter
    final HashMultiset<Symbol> counts = HashMultiset.create();

    // Process each file
    final SerifXMLLoader loader = SerifXMLLoader.fromStandardACETypes();
    log.info("Collecting counts from {} documents", inputFiles.size());
    for (final File file : inputFiles) {
      final DocTheory dt = loader.loadFrom(
          GZIPByteSource.fromCompressed(Files.asByteSource(file)).asCharSource(Charsets.UTF_8));
      final ICEWSEventMentions icewsEventMentions = dt.icewsEventMentions();
      for (final ICEWSEventMention eventMention : icewsEventMentions) {
        // Collapse count by top-level code
        counts.add(CAMEOCodes.truncateCode(eventMention.code()));
      }
    }

    // Output counts
    final Writer writer = outputSink.openBufferedStream();
    DelimUtils.writeDelimRow(writer, "Code", "Count");
    for (Multiset.Entry<Symbol> entry :  Multisets.copyHighestCountFirst(counts).entrySet()) {
      DelimUtils.writeDelimRow(writer, entry.getElement(), entry.getCount());
    }
    writer.close();
  }
}
