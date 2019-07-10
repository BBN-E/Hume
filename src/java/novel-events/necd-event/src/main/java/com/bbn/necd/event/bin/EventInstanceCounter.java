package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.common.symbols.SymbolUtils;
import com.bbn.necd.event.icews.CAMEOCodes;
import com.bbn.necd.event.icews.ICEWSEventInstance;
import com.bbn.necd.event.io.DelimUtils;
import com.google.common.base.Charsets;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSortedMap;
import com.google.common.collect.ImmutableSortedSet;
import com.google.common.collect.Maps;
import com.google.common.collect.Multiset;
import com.google.common.io.Files;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.util.List;
import java.util.Map;

import static com.bbn.necd.event.EventUtils.orderMapByReversedValues;
import static com.bbn.necd.event.io.CompressedFileUtils.readAsJsonList;

/**
 * Ouput counts for event instances.
 */
public final class EventInstanceCounter {

  private static final Logger log = LoggerFactory.getLogger(EventInstanceCounter.class);

  private static final Maps.EntryTransformer<Symbol, Multiset<Symbol>, Integer> multisetDistinctElements =
      new Maps.EntryTransformer<Symbol, Multiset<Symbol>, Integer>() {
        @Override
        public Integer transformEntry(Symbol key, Multiset<Symbol> value) {
          return value.elementSet().size();
        }
      };

  private static final Maps.EntryTransformer<Symbol, Multiset<Symbol>, Integer> multisetTotalElements =
      new Maps.EntryTransformer<Symbol, Multiset<Symbol>, Integer>() {
        @Override
        public Integer transformEntry(Symbol key, Multiset<Symbol> value) {
          return value.size();
        }
      };

  public static void main(final String[] args) throws IOException {
    if (args.length != 1) {
      System.err.println("Usage: eventInstanceCounter params");
      System.exit(1);
    }

    final Parameters params = Parameters.loadSerifStyle(new File(args[0]));
    final Parameters eventParams = params.copyNamespace("com.bbn.necd.event.extractor");
    final File eventsFile = eventParams.getExistingFile("extractedEvents");
    final File outputDir = eventParams.getAndMakeDirectory("extractedEventsCounts");

    // Read in events
    log.info("Reading events from {}", eventsFile);
    final ImmutableList<ICEWSEventInstance> events = readAsJsonList(eventsFile, ICEWSEventInstance.class);

    // Count the predicates per event code
    final Map<Symbol, Multiset<Symbol>> codePredicates = Maps.newHashMap();
    // Count the event codes per predicate
    final Map<Symbol, Multiset<Symbol>> predicateCodes = Maps.newHashMap();

    // Compute the counts
    for (final ICEWSEventInstance event : events) {
      // Skip events with no ICEWS info
      if (!event.getICEWSEventMentionInfo().isPresent()) {
        continue;
      }
      final Symbol code = CAMEOCodes.truncateCode(event.getICEWSEventMentionInfo().get().getCode());
      final Symbol predicate = event.getPredicate();
      // Add to counts, creating new multisets as needed
      // Code predicates
      createMultisetValueIfNeeded(code, codePredicates);
      codePredicates.get(code).add(predicate);
      // Predicate codes
      createMultisetValueIfNeeded(predicate, predicateCodes);
      predicateCodes.get(predicate).add(code);
    }

    log.info("Writing counts to directory {}", outputDir);

    // Codes and their predicates
    final ImmutableSortedMap<Symbol, Integer> codeUniquePredicateCounts = orderMapByReversedValues(
        Maps.transformEntries(codePredicates, multisetDistinctElements), SymbolUtils.byStringOrdering());
    final ImmutableSortedMap<Symbol, Integer> codeTotalCounts = orderMapByReversedValues(
        Maps.transformEntries(codePredicates, multisetTotalElements), SymbolUtils.byStringOrdering());
    final ImmutableSortedSet<Symbol> codes = codeTotalCounts.keySet();
    writeCountsCSV(codes, ImmutableList.of("Code", "Unique Predicates", "Total Predicates"),
        new File(outputDir, "code_predicates.csv"),
        ImmutableList.<Map<Symbol, Integer>>of(codeUniquePredicateCounts, codeTotalCounts));

    // Predicates and their codes
    final ImmutableSortedMap<Symbol, Integer> predicateUniqueCodeCounts = orderMapByReversedValues(
        Maps.transformEntries(predicateCodes, multisetDistinctElements), SymbolUtils.byStringOrdering());
    final ImmutableSortedMap<Symbol, Integer> predicateTotalCounts = orderMapByReversedValues(
        Maps.transformEntries(predicateCodes, multisetTotalElements), SymbolUtils.byStringOrdering());
    final ImmutableSortedSet<Symbol> predicates = predicateTotalCounts.keySet();
    writeCountsCSV(predicates, ImmutableList.of("Predicate", "Unique Codes", "Total Occurrences"),
        new File(outputDir, "predicate_codes.csv"),
        ImmutableList.<Map<Symbol, Integer>>of(predicateUniqueCodeCounts, predicateTotalCounts));

    // Raw data
    writeAllObservationsCSV(ImmutableList.of( "Predicate", "Code", "Count"), predicateCodes,
        new File(outputDir, "predicates.csv"));
  }

  private static void writeAllObservationsCSV(final ImmutableList<String> header,
      final Map<Symbol, Multiset<Symbol>> map, final File file) throws IOException {
    final Writer writer = Files.asCharSink(file, Charsets.UTF_8).openBufferedStream();
    DelimUtils.writeDelimRow(writer, header);

    for (final Symbol predicate : SymbolUtils.byStringOrdering().sortedCopy(map.keySet())) {
      final Multiset<Symbol> codes = map.get(predicate);
      for (final Multiset.Entry<Symbol> codeEntry : codes.entrySet()) {
        final Symbol code = codeEntry.getElement();
        final int count = codeEntry.getCount();
        DelimUtils.writeDelimRow(writer, predicate, code, count);
      }
    }

    writer.close();
  }

  private static void writeCountsCSV(final Iterable<Symbol> keys, final ImmutableList<String> header, final File file,
      final List<Map<Symbol, Integer>> maps)
      throws IOException {
    final Writer writer = Files.asCharSink(file, Charsets.UTF_8).openBufferedStream();
    DelimUtils.writeDelimRow(writer, header);
    for (final Symbol key : keys) {
      final ImmutableList.Builder<String> row = ImmutableList.builder();
      row.add(key.asString());
      for (final Map<Symbol, Integer> map : maps) {
        final int value = map.containsKey(key) ? map.get(key) : 0;
        row.add(Integer.toString(value));
      }
      DelimUtils.writeDelimRow(writer, row.build());
    }
    writer.close();
  }

  private static void createMultisetValueIfNeeded(final Symbol key, final Map<Symbol, Multiset<Symbol>> map) {
    if (!map.containsKey(key)) {
      map.put(key, HashMultiset.<Symbol>create());
    }
  }
}
