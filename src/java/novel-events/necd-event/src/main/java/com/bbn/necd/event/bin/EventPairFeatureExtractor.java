package com.bbn.necd.event.bin;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.common.symbols.SymbolUtils;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventPairFeatureGenerator;
import com.bbn.necd.event.features.EventPairFeatures;
import com.bbn.necd.event.features.PropositionTreeEvent;
import com.bbn.necd.event.io.EventWriter;
import com.bbn.necd.event.io.LabelWriter;
import com.bbn.necd.event.io.LabeledIdWriter;

import com.google.common.base.Charsets;
import com.google.common.base.Function;
import com.google.common.base.Stopwatch;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.sql.SQLException;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import static com.bbn.necd.event.EventUtils.loadProcessedEvents;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Generates features for event pairs selected by the sampler.
 */
public final class EventPairFeatureExtractor {

  private static final Logger log = LoggerFactory.getLogger(EventPairFeatureExtractor.class);

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

  public static void trueMain(final String[] argv) throws IOException, SQLException {
    if (argv.length != 1) {
      System.err.println("Usage: eventPairFeatureExtractor params");
      System.exit(1);
    }

    final Parameters params = Parameters.loadSerifStyle(new File(argv[0]));
    log.info("{} run on parameters:\n{}", EventPairFeatureExtractor.class, params.dump());

    final Parameters samplerParams = params.copyNamespace("com.bbn.necd.event.sampler");
    final Parameters featureParams = params.copyNamespace("com.bbn.necd.event.features");
    // Feature database sources
    final File wordNetParams = featureParams.getExistingFile("wordNetParams").getAbsoluteFile();
    final File icewsParams = featureParams.getExistingFile("icewsParams").getAbsoluteFile();

    // Input files
    final List<File> eventFeaturesFiles = FileUtils.loadFileList(samplerParams.getExistingFile("extractedEventFileList"));
    final File eventFeaturesDir = samplerParams.getExistingDirectory("extractedEventDir");
    featureParams.assertExactlyOneDefined("pairLabels", "eventsIds");

    // Output file
    final File eventFeaturesFile = featureParams.getCreatableFile("eventFeatures").getAbsoluteFile();
    final File pairFeaturesFile = featureParams.getCreatableFile("pairFeatures").getAbsoluteFile();

    // Create feature generator
    log.info("Creating feature generator");
    final EventPairFeatureGenerator generator = EventPairFeatureGenerator.create(Parameters.loadSerifStyle(wordNetParams),
        Parameters.loadSerifStyle(icewsParams));

    // Start timer
    final Stopwatch stopwatch = Stopwatch.createStarted();

    // We're either running on pair labels or just events
    if (featureParams.isPresent("pairLabels")) {
      final File pairLabelsTable = featureParams.getExistingFile("pairLabels");

      // Load ids from the table
      final ImmutableSet<Symbol> ids = getEventIds(pairLabelsTable);

      // Deserialize the event features and put them in an event id to features map
      final Map<Symbol, PropositionTreeEvent> eventFeaturesMap =
          loadProcessedEvents(ids, eventFeaturesFiles, eventFeaturesDir, log);

      // Generate features
      generatePairFeatures(generator, pairLabelsTable, eventFeaturesMap, eventFeaturesFile, pairFeaturesFile);

    } else if (featureParams.isPresent("eventsIds")) {
      // Do natural sample feature generation
      log.info("Generating features for natural event pairs");
      final File naturalIdFile = featureParams.getExistingFile("eventsIds");
      log.info("Loading event ids from {}", naturalIdFile);

      // Read in event ids
      final ImmutableSet<Symbol> ids = FluentIterable.from(
          LabeledIdWriter.getParser(naturalIdFile).getRecords())
          .transform(
              new Function<CSVRecord, Symbol>() {
                @Override
                public Symbol apply(final CSVRecord input) {
                  checkNotNull(input);
                  return Symbol.from(input.get(LabeledIdWriter.HEADER_ID));
                }
              })
          .toSet();

      FluentIterable.from(Files.readLines(naturalIdFile, Charsets.UTF_8))
          .transform(SymbolUtils.symbolizeFunction()).toSet();

      // Deserialize the event features and put them in an event id to features map
      final Map<Symbol, PropositionTreeEvent> eventFeaturesMap =
          loadProcessedEvents(ids, eventFeaturesFiles, eventFeaturesDir, log);

      // Write out the features
      generateAllPairFeatures(ids, generator, eventFeaturesMap, eventFeaturesFile, pairFeaturesFile);
    }

    // Close generator
    generator.close();

    // Output timing information
    stopwatch.stop();
    log.info("Feature extraction took {} seconds", stopwatch.elapsed(TimeUnit.SECONDS));
  }

  private static ImmutableSet<Symbol> getEventIds(final File pairLabelsTable) throws IOException {
    final CSVParser pairTableReader = LabelWriter.getParser(pairLabelsTable);
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();
    for (final CSVRecord row : pairTableReader) {
      // Get event ids
      ret.add(Symbol.from(row.get(0)));
      ret.add(Symbol.from(row.get(1)));
    }
    return ret.build();
  }

  private static void generatePairFeatures(final EventPairFeatureGenerator generator, final File pairLabelsTable,
      Map<Symbol, PropositionTreeEvent> eventFeatures, final File eventFeaturesFile,
      final File pairFeaturesTable) throws IOException {

    // Open the output
    final EventWriter eventWriter = EventWriter.create(eventFeaturesFile, pairFeaturesTable);

    // Open the label table
    log.info("Reading event pair labels from {}", pairLabelsTable);
    final CSVParser pairTableReader = LabelWriter.getParser(pairLabelsTable);

    // Process each pair
    log.info("Writing event pair features");
    int pairCount = 0;
    for (final CSVRecord row : pairTableReader) {
      // Get event ids
      final Symbol id1 = Symbol.from(row.get(0));
      final Symbol id2 = Symbol.from(row.get(1));

      // Generate event features
      final PropositionTreeEvent event1 = eventFeatures.get(id1);
      final EventFeatures event1Features = generator.generate(event1);
      final PropositionTreeEvent event2 = eventFeatures.get(id2);
      final EventFeatures event2Features = generator.generate(event2);

      // Generate pair features
      final EventPairFeatures pairFeatures = generator.generate(event1, event2);

      // Write them out
      eventWriter.addIfNeeded(event1Features);
      eventWriter.addIfNeeded(event2Features);
      eventWriter.add(pairFeatures);
      pairCount++;
    }

    // Close the output
    eventWriter.close();
    log.info("Wrote features for {} event pairs", pairCount);
    log.info("Wrote pair features to {}", pairFeaturesTable);
    log.info("Wrote event features to {}", eventFeaturesFile);
  }

  private static void generateAllPairFeatures(final ImmutableSet<Symbol> ids, final EventPairFeatureGenerator generator,
      final Map<Symbol, PropositionTreeEvent> eventFeatures, final File eventFeaturesFile,
      final File pairFeaturesFile) throws IOException {

    // Open the output
    final EventWriter eventWriter = EventWriter.create(eventFeaturesFile, pairFeaturesFile);

    // Process each pair
    log.info("Writing event pair features for all pairs from {} events", ids.size());
    long pairCount = 0;
    // Since we don't need (a, b) and (b, a) we simply pair each event with all following events, i.e. for A-D
    // (A, B) (A, C) (A, D) (B, C) (B, D)
    final ImmutableList<Symbol> idList = ImmutableList.copyOf(ids);
    final int nIds = idList.size();
    // (nIds - 1) since the last pair starts with the next to last item
    for (int i = 0; i < (nIds - 1); i++) {
      final Symbol id1 = idList.get(i);
      for (int j = i + 1; j < nIds; j++) {
        final Symbol id2 = idList.get(j);

        // Generate event features
        final PropositionTreeEvent event1 = eventFeatures.get(id1);
        final EventFeatures event1Features = generator.generate(event1);
        final PropositionTreeEvent event2 = eventFeatures.get(id2);
        final EventFeatures event2Features = generator.generate(event2);

        // Generate pair features
        final EventPairFeatures pairFeatures = generator.generate(event1, event2);

        // Write them out
        eventWriter.addIfNeeded(event1Features);
        eventWriter.addIfNeeded(event2Features);
        eventWriter.add(pairFeatures);
        pairCount++;

        if (pairCount % 100000 == 0) {
          log.info("Wrote {} pair features", pairCount);
        }
      }
    }

    // Write the output
    eventWriter.close();
    log.info("Wrote features for {} event pairs", pairCount);
    log.info("Wrote pair features to {}", pairFeaturesFile);
    log.info("Wrote event features to {}", eventFeaturesFile);
  }
}
