package com.bbn.necd.event.bin;

import com.bbn.bue.common.StringUtils;
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
import com.google.common.io.Files;
import com.google.common.io.LineProcessor;
import com.google.common.primitives.Doubles;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.List;

import static com.bbn.necd.event.EventUtils.loadProcessedEvents;
import static com.google.common.base.Preconditions.checkArgument;

/**
 * Prunes away non-events based on predictions from the event/non-event (ENE) classifier.
 */
public final class EventPruner {

  private static final Logger log = LoggerFactory.getLogger(EventPruner.class);

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
      System.err.println("Usage: eventPruner params");
      System.exit(1);
    }

    final Parameters allParams = Parameters.loadSerifStyle(new File(argv[0]));
    log.info("{} run on parameters:\n{}", EventPruner.class, allParams.dump());
    final Parameters params = allParams.copyNamespace("com.bbn.necd.event.pruner");
    // Input
    final File predictions = params.getExistingFile("predictions");
    final File inputIds = params.getExistingFile("inputIds");
    final File inputEvents = params.getExistingFile("inputEvents");

    // Output
    final File outputIds = params.getCreatableFile("outputIds");
    final File outputEvents = params.getCreatableFile("outputEvents");

    // Load the ids
    log.info("Loading ids from {}", inputIds);
    final ImmutableList<Symbol> ids = FluentIterable.from(Files.readLines(inputIds, Charsets.UTF_8))
        .transform(SymbolUtils.symbolizeFunction())
        .toList();
    log.info("Loaded {} ids", ids.size());

    // Get the ids to keep
    log.info("Loading predictions from {}", predictions);
    final ImmutableSet<Symbol> selectedIds =
        Files.readLines(predictions, Charsets.UTF_8, new PredictionsProcessor(ids));
    log.info("Loaded {} positive predictions", selectedIds.size());

    // Load the events
    log.info("Loading events from {}", inputEvents);
    // Set true so that all ACCENT-coded events pass through
    final ImmutableMap<Symbol, PropositionTreeEvent> events =
        loadProcessedEvents(ImmutableSet.copyOf(selectedIds), inputEvents, false);
    log.info("Loaded {} events", events.size());

    // Write out ids
    log.info("Writing selected ids to {}", outputIds);
    Files.asCharSink(outputIds, Charsets.UTF_8).writeLines(
        FluentIterable.from(selectedIds).transform(SymbolUtils.desymbolizeFunction()));

    // Write out events
    log.info("Writing selected events to {}", outputEvents);
    CompressedFileUtils.writeAsJson(events.values(), outputEvents);
  }

  private static class PredictionsProcessor implements LineProcessor<ImmutableSet<Symbol>> {

    private ImmutableList<Symbol> originalIds;
    private ImmutableSet.Builder<Symbol> outputIds;
    private int lineNum;

    private PredictionsProcessor(final ImmutableList<Symbol> ids) {
      this.originalIds = ids;
      outputIds = ImmutableSet.builder();
    }

    @Override
    public boolean processLine(final String line) throws IOException {
      // Process every line except the first, which is a header
      if (lineNum != 0) {
        final List<String> splits = StringUtils.onSpaces().splitToList(line);
        checkArgument(splits.size() > 0, "Empty line");
        final Integer label = Integer.valueOf(splits.get(0));
        checkArgument(label == 1 || label == -1, "Label must be +1 or -1");
        // If the label is one, carry the correct id over to the output
        final double positiveScore = Doubles.tryParse(splits.get(1)).doubleValue();
        if (label == 1 && positiveScore>=0.80) {
          // lineNum 1 is the first id, so we subtract one from the lineNum to get the index
          outputIds.add(originalIds.get(lineNum - 1));
        }
      }

      lineNum++;
      return true;
    }

    @Override
    public ImmutableSet<Symbol> getResult() {
      return outputIds.build();
    }
  }
}
