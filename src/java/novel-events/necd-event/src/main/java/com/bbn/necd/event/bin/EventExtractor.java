package com.bbn.necd.event.bin;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.io.GZIPByteSource;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.parameters.ParametersModule;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.common.symbols.SymbolUtils;
import com.bbn.necd.event.features.PropositionTreeEvent;
import com.bbn.necd.event.features.WordNetWrapper;
import com.bbn.necd.event.propositions.PropositionTreeEventInstanceExtractor;
import com.bbn.necd.event.propositions.PropositionTreeEventInstanceExtractor.GenerationMethod;
import com.bbn.necd.event.propositions.PropositionTreeEventProcessor;
import com.bbn.necd.event.wrappers.ExtractedPropositionTreeEventInfo;
import com.bbn.nlp.banks.wordnet.IWordNet;
import com.bbn.nlp.banks.wordnet.WordNetM;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.base.Stopwatch;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import com.google.common.io.Files;
import com.google.inject.Guice;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.concurrent.TimeUnit;

import static com.bbn.necd.event.io.CompressedFileUtils.writeAsJson;

public final class EventExtractor {

  private static final Logger log = LoggerFactory.getLogger(EventExtractor.class);

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

  public static void trueMain(final String[] argv) throws IOException {
    if (argv.length != 1) {
      System.err.println("Usage: eventInstanceExtractor params");
      System.exit(1);
    }
    final Parameters params = Parameters.loadSerifStyle(new File(argv[0]));
    log.info("{} run on parameters:\n{}", EventExtractor.class, params.dump());

    final Parameters eventParams = params.copyNamespace("com.bbn.necd.event.extractor");
    // Input
    final List<File> inputFiles = FileUtils.loadFileList(eventParams.getExistingFile("serifXmlFileList"));

    // Configuration
    final GenerationMethod generationMethod = eventParams.getEnum("generationMethod", GenerationMethod.class);
    final int maxHops = eventParams.getPositiveInteger("maxHops");

    // WordNet
    final File wordNetParamFile = params.copyNamespace("com.bbn.necd.event.features")
        .getExistingFile("wordNetParams").getAbsoluteFile();

    // Output
    final File extractedEventsFiles = eventParams.getCreatableFile("extractedEvents");
    final File processedEventsFile = eventParams.getCreatableFile("processedEvents");
    final Optional<File> eventIdFile = eventParams.getOptionalCreatableFile("eventIds");

    final PropositionTreeEventInstanceExtractor extractor =
        PropositionTreeEventInstanceExtractor.create(generationMethod, maxHops);

    final SerifXMLLoader loader = SerifXMLLoader.builderFromStandardACETypes().allowSloppyOffsets().build();

    // Load WordNet params
    final Parameters wordNetParams = Parameters.loadSerifStyle(wordNetParamFile);
    final ParametersModule paramsModule = ParametersModule.createAndDump(wordNetParams);
    final IWordNet wordNet = Guice.createInjector(
        paramsModule, WordNetM.fromParameters(wordNetParams)).getInstance(IWordNet.class);
    // We don't care about similarity so we pass null
    final WordNetWrapper wn = WordNetWrapper.fromWordNet(wordNet, null, null);

    log.info("Extracting event instances from {} files", inputFiles.size());
    final Stopwatch stopwatch = Stopwatch.createStarted();
    for (final File input : inputFiles) {
      final DocTheory dt = loader.loadFrom(
          GZIPByteSource.fromCompressed(Files.asByteSource(input)).asCharSource(Charsets.UTF_8));
      extractor.process(dt);
    }
    final ImmutableList<ExtractedPropositionTreeEventInfo> extractedEvents =
        extractor.getSerializableEvents();
    final long elapsed = stopwatch.elapsed(TimeUnit.MILLISECONDS);
    log.info("Extraction took {} seconds ({} milliseconds per document)",
        elapsed / 1000.0, elapsed / (float) inputFiles.size());

    log.info("Writing {} events to {}", extractedEvents.size(),  extractedEventsFiles);
    writeAsJson(extractedEvents, extractedEventsFiles);

    // Print statistics
    extractor.finish();

    // Transform the events
    final PropositionTreeEventProcessor processor = PropositionTreeEventProcessor.from(params);
    for (final ExtractedPropositionTreeEventInfo event : extractedEvents) {
      processor.process(event, wn);
    }
    final ImmutableList<PropositionTreeEvent> processedEvents =
        processor.getSerializableEvents();
    // Write transformed events
    log.info("Writing {} processed events to {}", processedEvents.size(), processedEventsFile);
    writeAsJson(processedEvents, processedEventsFile);

    final ImmutableList.Builder<Symbol> idBuilder = ImmutableList.builder();
    for (final PropositionTreeEvent extracted : processedEvents) {
      idBuilder.add(extracted.getId());
    }
    final ImmutableList<Symbol> ids = idBuilder.build();

    if (eventIdFile.isPresent()) {
      final File idFile = eventIdFile.get();
      log.info("Writing {} IDs to {}", ids.size(), idFile);
      Files.asCharSink(idFile, Charsets.UTF_8).writeLines(
          Lists.transform(ids, SymbolUtils.desymbolizeFunction()));
    }

    // Wrap up
    processor.finish();
  }
}
