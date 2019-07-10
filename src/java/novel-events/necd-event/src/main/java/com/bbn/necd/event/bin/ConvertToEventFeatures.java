package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventPairFeatureGenerator;
import com.bbn.necd.event.features.PropositionTreeEvent;
import com.bbn.necd.event.io.CompressedFileUtils;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.sql.SQLException;

/**
 * Created by ychan on 5/19/16.
 * Convert PropositionTreeEvent to EventFeatures, for a given set of event candidate IDs
 */
public final class ConvertToEventFeatures {
  private static final Logger log = LoggerFactory.getLogger(DoTraining.class);

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

  public static void trueMain(final String[] argv) throws IOException, ClassNotFoundException,
                                                          SQLException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final Parameters featureParams = params.copyNamespace("com.bbn.necd.event.features");
    // Feature database sources
    final File wordNetParams = featureParams.getExistingFile("wordNetParams").getAbsoluteFile();
    final File icewsParams = featureParams.getExistingFile("icewsParams").getAbsoluteFile();

    final EventPairFeatureGenerator generator = EventPairFeatureGenerator.create(Parameters.loadSerifStyle(wordNetParams),
        Parameters.loadSerifStyle(icewsParams));

    final ImmutableMap<Symbol, PropositionTreeEvent> events = readEvents(params.getExistingFile("propositionTreeEventFile"));

    final ImmutableSet<Symbol> targetIds = readTargetIds(params.getExistingFile("ene.annotation.ecIds"));

    // tagetIds are those extracted from the ENE annotation XML files
    final ImmutableList<EventFeatures> examples = convertTargetEvents(generator, events, targetIds);

    CompressedFileUtils.writeAsJson(examples, params.getCreatableFile("ere.annotation.eventFeatures"));
  }

  private static ImmutableList<EventFeatures> convertTargetEvents(final EventPairFeatureGenerator generator,
      final ImmutableMap<Symbol, PropositionTreeEvent> events, final ImmutableSet<Symbol> targetIds) {
    final ImmutableList.Builder<EventFeatures> ret = ImmutableList.builder();

    for(final Symbol id : targetIds) {
      final EventFeatures eg = generator.generate(events.get(id));
      ret.add(eg);
    }

    return ret.build();
  }

  private static ImmutableSet<Symbol> readTargetIds(final File infile) throws IOException {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    for(final String line : Files.asCharSource(infile, Charsets.UTF_8).readLines()) {
      ret.add(Symbol.from(line));
    }

    return ret.build();
  }

  public static ImmutableMap<Symbol, PropositionTreeEvent> readEvents(final File infile)
      throws IOException {
    final ImmutableMap.Builder<Symbol, PropositionTreeEvent> ret = ImmutableMap.builder();

    final ImmutableList<PropositionTreeEvent> events =
        CompressedFileUtils.readAsJsonList(infile, PropositionTreeEvent.class);

    for(final PropositionTreeEvent eg : events) {
      ret.put(eg.getId(), eg);
    }

    return ret.build();
  }

}
