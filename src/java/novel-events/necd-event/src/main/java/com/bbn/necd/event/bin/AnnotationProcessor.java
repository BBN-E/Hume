package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.common.symbols.SymbolUtils;
import com.bbn.necd.event.features.PropositionTreeEvent;
import com.bbn.necd.event.io.CompressedFileUtils;

import com.google.common.base.Charsets;
import com.google.common.base.Preconditions;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.util.Collections;
import java.util.List;

import static com.bbn.necd.event.EventUtils.loadProcessedEvents;

/**
 * Processes negative/positive ENE annotation examples.
 */
public final class AnnotationProcessor {

  private static final Logger log = LoggerFactory.getLogger(AnnotationProcessor.class);

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
      System.err.println("Usage: annotationProcessor params");
      System.exit(1);
    }

    final Parameters allParams = Parameters.loadSerifStyle(new File(argv[0]));
    log.info("{} run on parameters:\n{}", AnnotationProcessor.class, allParams.dump());

    final Parameters params = allParams.copyNamespace("com.bbn.necd.event.annotation");
    // Input
    final File positiveFile = params.getExistingFile("positive.ids");
    final File negativeFile = params.getExistingFile("negative.ids");
    final File baseDir = params.getExistingDirectory("extractedEventDir");
    final File eventFile = params.getPossiblyNonexistentFile("processedEventFile");

    // Output
    final File annotationIdsFile = params.getCreatableFile("all.ids");
    final File annotationLabelsFile = params.getCreatableFile("all.labels");
    final File annotationEventsFile = params.getCreatableFile("all.events");

    // Load the ids
    final List<String> positiveIds = Files.readLines(positiveFile, Charsets.UTF_8);
    final List<String> negativeIds = Files.readLines(negativeFile, Charsets.UTF_8);
    final ImmutableList<String> ids = ImmutableList.<String>builder()
        .addAll(positiveIds)
        .addAll(negativeIds)
        .build();
    log.info("Loaded {} annotated ids ({} positive, {} negative)", ids.size(), positiveIds.size(),
        negativeIds.size());

    // Load the relevant events
    final ImmutableSet<Symbol> idSet = FluentIterable.from(ids)
        .transform(SymbolUtils.symbolizeFunction())
        .toSet();
    Preconditions.checkState(idSet.size() == ids.size(),
        "Some IDs appear both in positive and negative lists");
    final ImmutableMap<Symbol, PropositionTreeEvent> selectedEvents =
        loadProcessedEvents(idSet, ImmutableList.of(eventFile), baseDir, log);
    log.info("Loaded {} extracted events", selectedEvents.size());

    // Write out ids
    log.info("Writing annotated ids to {}", annotationIdsFile);
    Files.asCharSink(annotationIdsFile, Charsets.UTF_8).writeLines(ids);

    // Write out labels. As the ids are all positive first, then negative, we can just repeat the
    // positive/negative labels.
    final ImmutableList<String> labels = ImmutableList.<String>builder()
        .addAll(Collections.nCopies(positiveIds.size(), "+1"))
        .addAll(Collections.nCopies(negativeIds.size(), "-1"))
        .build();
    log.info("Writing annotated ids and labels to {}", annotationLabelsFile);
    Preconditions.checkState(labels.size() == ids.size());
    try (final Writer writer =
        Files.asCharSink(annotationLabelsFile, Charsets.UTF_8).openBufferedStream()) {
      for (int i = 0; i < ids.size(); i++) {
        writer.write(ids.get(i) + '\t' + labels.get(i) + '\n');
      }
    }

    // Write out events
    log.info("Writing selected events to {}", annotationEventsFile);
    CompressedFileUtils.writeAsJson(selectedEvents.values(), annotationEventsFile);
  }
}
