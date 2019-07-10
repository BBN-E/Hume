package com.bbn.necd.event.bin;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.common.symbols.SymbolUtils;
import com.bbn.necd.event.features.PropositionTreeEvent;
import com.bbn.necd.event.io.CompressedFileUtils;

import com.google.common.base.Charsets;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.Random;

import static com.bbn.necd.event.EventUtils.loadProcessedEvents;

/**
 * Downsamples processed events
 */
public final class EventDownsampler {

  private static final Logger log = LoggerFactory.getLogger(EventDownsampler.class);

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

  public static void trueMain(String[] argv) throws IOException {
    if (argv.length != 1) {
      System.err.println("Usage: eventDownsampler params");
      System.exit(1);
    }

    final Parameters params = Parameters.loadSerifStyle(new File(argv[0]));
    log.info("{} run on parameters:\n{}", EventDownsampler.class, params.dump());
    final Parameters downsamplerParams = params.copyNamespace("com.bbn.necd.event.downsampler");
    // Input
    final int randomSeed = downsamplerParams.getInteger("randomSeed");
    final int downsampleSize = downsamplerParams.getInteger("downsampleSize");
    final File baseDir = downsamplerParams.getExistingDirectory("extractedEventDir");
    final ImmutableList<File> idFiles =
        FileUtils.loadFileList(downsamplerParams.getExistingFile("eventIdFileList"));
    final ImmutableList<File> eventFiles =
        FileUtils.loadFileList(downsamplerParams.getExistingFile("processedEventFileList"));
    // Output
    final File downsampledIdFile = downsamplerParams.getCreatableFile("downsampledIdsFile");
    final File downsampledEventsFile = downsamplerParams.getCreatableFile("downsampledEventsFile");

    // Load the ids into a mutable list to ease later shuffling
    final List<String> ids = Lists.newArrayList();
    for (final File idFile : idFiles) {
      final File fullIdFile = new File(baseDir, idFile.toString());
      log.info("Loading ids from {}", fullIdFile);
      ids.addAll(Files.readLines(fullIdFile, Charsets.UTF_8));
    }
    log.info("Loaded {} ids", ids.size());

    // Shuffle ids
    Collections.shuffle(ids, new Random(randomSeed));

    // Add the first ids to a new set
    log.info("Downsampling to {} ids", downsampleSize);
    final ImmutableSet<Symbol> selectedIds = FluentIterable.from(ids)
        .limit(downsampleSize)
        .transform(SymbolUtils.symbolizeFunction())
        .toSet();

    // Load the relevant events
    final ImmutableMap<Symbol, PropositionTreeEvent> selectedEvents =
        loadProcessedEvents(selectedIds, eventFiles, baseDir, log);

    // Write out ids
    log.info("Writing selected ids to {}", downsampledIdFile);
    Files.asCharSink(downsampledIdFile, Charsets.UTF_8).writeLines(
        FluentIterable.from(selectedIds).transform(SymbolUtils.desymbolizeFunction()));

    // Write out events
    log.info("Writing selected events to {}", downsampledEventsFile);
    CompressedFileUtils.writeAsJson(selectedEvents.values(), downsampledEventsFile);
  }
}
