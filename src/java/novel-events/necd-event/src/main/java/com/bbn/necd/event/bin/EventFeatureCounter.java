package com.bbn.necd.event.bin;

import com.bbn.bue.common.collections.CollectionUtils;
import com.bbn.bue.common.primitives.IntUtils;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.features.EventFeaturesUtils;
import com.bbn.necd.event.features.PropositionTreeEvent;
import com.bbn.necd.event.propositions.EventFilter;
import com.bbn.necd.event.propositions.PropositionPredicateType;
import com.google.common.base.Charsets;
import com.google.common.base.Function;
import com.google.common.base.Joiner;
import com.google.common.base.Predicate;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableMultiset;
import com.google.common.collect.Maps;
import com.google.common.collect.Multiset;
import com.google.common.collect.Multisets;
import com.google.common.collect.Ordering;
import com.google.common.io.Files;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.util.Map;

import static com.bbn.bue.common.StringUtils.NewlineJoiner;
import static com.bbn.bue.common.StringUtils.SpaceJoiner;
import static com.bbn.necd.event.io.CompressedFileUtils.readAsJsonList;
import static com.google.common.base.Preconditions.checkNotNull;
import static com.google.common.base.Predicates.not;

/**
 * Output counts and information for serialized event features.
 */
public final class EventFeatureCounter {

  private static final Logger log = LoggerFactory.getLogger(EventFeatureCounter.class);

  public static void main(final String[] args) throws IOException {
    if (args.length != 4) {
      System.out.println("Usage: eventFeatureCounter events noun_output verb_output event_output");
      System.exit(1);
    }
    final File eventFile = new File(args[0]);
    final File nounFile = new File(args[1]);
    final File verbFile = new File(args[2]);
    final File eventOutputFile = new File(args[3]);
    log.info("Loading events from {}", eventFile);
    final ImmutableList<PropositionTreeEvent> events =
        readAsJsonList(eventFile, PropositionTreeEvent.class);
    log.info("Loaded {} events", events.size());

    // Count the codes, if they're present
    final ImmutableList<PropositionTreeEvent> uncodedEvents = FluentIterable.from(events)
        .filter(not(HasCodePredicate.INSTANCE)).toList();
    final ImmutableMultimap<Symbol, PropositionTreeEvent> codeEvents = EventFeaturesUtils.codeFeaturesMap(events);
    final Map<Symbol, Integer> codeCounts = Maps.transformValues(codeEvents.asMap(), CollectionUtils.sizeFunction());
    final long totalCoded = IntUtils.sum(codeCounts.values());
    log.info("Total events: {}", events.size());
    log.info("Coded events: {} ({}%)", totalCoded, String.format("%.2f", 100.0 * totalCoded / events.size()));

    // Count by event filter
    final ImmutableList<PropositionTreeEvent> filterSimple =
        FluentIterable.from(events).filter(EventFilterPredicate.on(EventFilter.SIMPLE)).toList();
    log.info("EventFilter.SIMPLE events: {}", filterSimple.size());
    final ImmutableList<PropositionTreeEvent> filterAll =
        FluentIterable.from(events).filter(EventFilterPredicate.on(EventFilter.ALL)).toList();
    log.info("EventFilter.ALL events: {}", filterAll.size());

    // Count the predicates by noun and verb separately
    final ImmutableList<PropositionTreeEvent> verbs =
        FluentIterable.from(events).filter(PredicateTypePredicate.on(PropositionPredicateType.VERB)).toList();
    log.info("Verb-rooted events: {}", verbs.size());
    final ImmutableList<PropositionTreeEvent> nouns =
        FluentIterable.from(events).filter(PredicateTypePredicate.on(PropositionPredicateType.NOUN)).toList();
    log.info("Noun-rooted events: {}", nouns.size());

    // Count each group by hops
    log.info("Overall hop counts:");
    printHopCounts(events);
    log.info("Coded hop counts:");
    printHopCounts(codeEvents.values());
    log.info("Uncoded hop counts:");
    printHopCounts(uncodedEvents);

    log.info("Writing nouns to {}", nounFile);
    writePredicateCounts(nouns, nounFile);
    log.info("Writing verbs to {}", verbFile);
    writePredicateCounts(verbs, verbFile);
    log.info("Writing events to {}", eventOutputFile);
    writeEvents(events, eventOutputFile);
  }

  private static void printHopCounts(Iterable<PropositionTreeEvent> events) {
    final HashMultiset<Integer> hopCounts =
        HashMultiset.create(FluentIterable.from(events).transform(HopCountFunction.INSTANCE));
    for (int hopCount : Ordering.natural().sortedCopy(hopCounts.elementSet())) {
      System.out.println(hopCount + "\t" + hopCounts.count(hopCount));
    }
  }

  private static void writePredicateCounts(final ImmutableList<PropositionTreeEvent> events,
      final File output) throws IOException {
    try (final Writer writer = Files.asCharSink(output, Charsets.UTF_8).openBufferedStream()) {
      final ImmutableMultiset<ImmutableList<Symbol>> predicateCounts = Multisets.copyHighestCountFirst(
          ImmutableMultiset.copyOf(FluentIterable.from(events).transform(EventPredicateFunction.INSTANCE)));
      final Joiner tabJoiner = Joiner.on("\t");
      for (final Multiset.Entry<ImmutableList<Symbol>> entry : predicateCounts.entrySet()) {
        writer.write(tabJoiner.join(entry.getCount(), entry.getElement()) + "\n");
      }
    }
  }

  private static void writeEvents(final ImmutableList<PropositionTreeEvent> events, final File output)
      throws IOException {
    try (final Writer writer = Files.asCharSink(output, Charsets.UTF_8).openBufferedStream()) {
      for (final PropositionTreeEvent event : events) {
        writer.write(summarizeEvent(event));
        writer.write("\n\n");
      }
    }
  }

  private static String summarizeEvent(PropositionTreeEvent event) {
    final ImmutableList.Builder<String> lines = ImmutableList.builder();
    lines.add("Filter: " + event.getEventFilter());
    lines.add("Source: " + SpaceJoiner.join(event.getSourceTokens()));
    lines.add("Target: " + SpaceJoiner.join(event.getTargetTokens()));
    lines.add("Predicates: " + event.getPredicates() + " (" + event.getPredType() + " root)");
    return NewlineJoiner.join(lines.build());
  }

  private enum EventPredicateFunction implements Function<PropositionTreeEvent, ImmutableList<Symbol>> {
    INSTANCE;

    @Override
    public ImmutableList<Symbol> apply (PropositionTreeEvent input){
      checkNotNull(input);
      return input.getPredicates();
    }
  }

  private static class PredicateTypePredicate implements Predicate<PropositionTreeEvent> {

    private final PropositionPredicateType value;

    private PredicateTypePredicate(PropositionPredicateType value) {
      this.value = value;
    }

    public static PredicateTypePredicate on(PropositionPredicateType value) {
      return new PredicateTypePredicate(value);
    }

    @Override
    public boolean apply(PropositionTreeEvent input) {
      checkNotNull(input);
      return value.equals(input.getPredType());
    }
  }

  private static class EventFilterPredicate implements Predicate<PropositionTreeEvent> {

    private final EventFilter value;

    private EventFilterPredicate(EventFilter value) {
      this.value = value;
    }

    public static EventFilterPredicate on(EventFilter filter) {
      return new EventFilterPredicate(filter);
    }

    @Override
    public boolean apply(PropositionTreeEvent input) {
      checkNotNull(input);
      return value.equals(input.getEventFilter());
    }
  }

  private enum HasCodePredicate implements Predicate<PropositionTreeEvent> {
    INSTANCE;

    @Override
    public boolean apply(PropositionTreeEvent input) {
      checkNotNull(input);
      return input.getEventCode().isPresent();
    }
  }

  private enum HopCountFunction implements Function<PropositionTreeEvent, Integer> {
    INSTANCE;

    @Override
    public Integer apply(PropositionTreeEvent input) {
      checkNotNull(input);
      return input.getHops();
    }
  }
}
