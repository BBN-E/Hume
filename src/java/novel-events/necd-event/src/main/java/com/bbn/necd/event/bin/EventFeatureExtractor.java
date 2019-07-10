package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventPairFeatureGenerator;
import com.bbn.necd.event.features.PropositionTreeEvent;
import com.bbn.necd.event.io.CompressedFileUtils;

import com.google.common.base.Stopwatch;
import com.google.common.collect.ImmutableList;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.sql.SQLException;
import java.util.concurrent.TimeUnit;

/**
 * Generates features for individual events to be used by the ENE classifier.
 */
public final class EventFeatureExtractor {

  private static final Logger log = LoggerFactory.getLogger(EventFeatureExtractor.class);

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
      System.err.println("Usage: eventFeatureExtractor params");
      System.exit(1);
    }

    final Parameters params = Parameters.loadSerifStyle(new File(argv[0]));
    log.info("{} run on parameters:\n{}", EventFeatureExtractor.class, params.dump());

    final Parameters eventFeaturesParams = params.copyNamespace("com.bbn.necd.event.eventFeatures");
    final Parameters featureParams = params.copyNamespace("com.bbn.necd.event.features");
    // Input
    final File eventsFile = eventFeaturesParams.getCreatableFile("eventsFile");
    // Output
    final File eventFeaturesFile = eventFeaturesParams.getCreatableFile("eventFeaturesFile");
    // Feature database sources
    final File wordNetParams = featureParams.getExistingFile("wordNetParams").getAbsoluteFile();
    final File icewsParams = featureParams.getExistingFile("icewsParams").getAbsoluteFile();

    // Deserialize the event features and put them in an event id to features map
    final ImmutableList<PropositionTreeEvent> events =
        CompressedFileUtils.readAsJsonList(eventsFile, PropositionTreeEvent.class);

    // Create feature generator
    log.info("Creating feature generator");
    final EventPairFeatureGenerator generator = EventPairFeatureGenerator.create(
        Parameters.loadSerifStyle(wordNetParams), Parameters.loadSerifStyle(icewsParams));


    // Generate features
    log.info("Generating features");
    final Stopwatch stopwatch = Stopwatch.createStarted();
    final ImmutableList.Builder<EventFeatures> featuresBuilder = ImmutableList.builder();
    for (final PropositionTreeEvent event : events) {
      featuresBuilder.add(generator.generate(event));
    }

    // Wrap up
    final ImmutableList<EventFeatures> features = featuresBuilder.build();
    stopwatch.stop();
    log.info("Feature extraction for {} events took {} seconds", features.size(),
        stopwatch.elapsed(TimeUnit.SECONDS));

    // Write out
    log.info("Writing output to {}", eventFeaturesFile);
    CompressedFileUtils.writeAsJson(features, eventFeaturesFile);

    // Close generator
    generator.close();
  }
}
