package com.bbn.necd.event.propositions;

import com.bbn.bue.common.Finishable;
import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.TheoryUtils;
import com.bbn.necd.event.icews.ActorMentionFilter;
import com.bbn.necd.event.icews.ActorType;
import com.bbn.necd.event.icews.ICEWSActors;
import com.bbn.necd.event.wrappers.ExtractedPropositionTreeEventInfo;
import com.bbn.necd.event.wrappers.MentionInfo;
import com.bbn.necd.event.wrappers.MentionPair;
import com.bbn.necd.event.wrappers.MentionSpanEquivalence;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.Proposition.MentionArgument;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.actors.ActorMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMentions;

import com.google.common.base.Equivalence;
import com.google.common.base.Optional;
import com.google.common.base.Predicate;
import com.google.common.base.Predicates;
import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.BiMap;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.ImmutableBiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Maps;
import com.google.common.collect.Multimap;
import com.google.common.collect.Multimaps;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collection;
import java.util.Set;

import static com.bbn.necd.event.TheoryUtils.actorMentionMatchesSentence;
import static com.bbn.necd.event.TheoryUtils.actorMentionMentionFunction;
import static com.bbn.necd.event.icews.ICEWSActors.ROLE_SOURCE;
import static com.bbn.necd.event.icews.ICEWSActors.ROLE_TARGET;
import static com.bbn.necd.event.icews.ICEWSActors.extractMentionPairFunction;
import static com.bbn.necd.event.icews.ICEWSActors.getParticipant;
import static com.bbn.necd.event.icews.ICEWSActors.icewsEventMentionOnlyContainsActorMentions;
import static com.bbn.necd.event.icews.ICEWSActors.isAcceptableICEWSEventMention;
import static com.bbn.necd.event.icews.ICEWSActors.isProperOrCompositeActorMention;
import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkState;

/**
 * A proposition tree-based event instance generator.
 */
public final class PropositionTreeEventInstanceExtractor implements Finishable {

  private static final Logger log = LoggerFactory.getLogger(PropositionTreeEventInstanceExtractor.class);
  private static final boolean DEBUG_LOGGING = false;

  private static final String UNHANDLED_MSG = "Unhandled generation method";

  private static final Symbol ROOT_NOUN_ROLE = Symbol.from("OTH");

  private int documentCount = 0;
  private int sentenceCount = 0;
  private int sentenceWithRootPropCount = 0;
  private int rootPropCount = 0;
  private int icewsEventCount = 0;
  private int icewsEligibleEventCount = 0;
  private int icewsEligibleMatched = 0;
  private int generatedEvents = 0;

  private final GenerationMethod generationMethod;
  private final int maxHops;

  private ImmutableList.Builder<ExtractedPropositionTreeEventInfo> serializableEvents;

  private PropositionTreeEventInstanceExtractor(final GenerationMethod method, final int maxHops) {
    this.generationMethod = method;
    this.maxHops = maxHops;
    serializableEvents = ImmutableList.builder();
  }

  public static PropositionTreeEventInstanceExtractor create(final GenerationMethod method, final int maxHops) {
    return new PropositionTreeEventInstanceExtractor(method, maxHops);
  }

  public void process(DocTheory dt) {
    documentCount++;

    // Get ICEWS events
    final ICEWSEventMentions allICEWSEvents = dt.icewsEventMentions();
    icewsEventCount += allICEWSEvents.size();

    // Filter down to acceptable events. These will be counted later after further filtering.
    final ImmutableList<ICEWSEventMention> eligibleICEWSEvents = ImmutableList.copyOf(
        Iterables.filter(allICEWSEvents, isAcceptableICEWSEventMention()));

    // Get document-level ActorMentions
    final ImmutableList<ActorMention> docActorMentions = ImmutableList.copyOf(dt.actorMentions());

    // Process each sentence
    for (final SentenceTheory st : dt.nonEmptySentenceTheories()) {
      sentenceCount++;

      // Get the sentence propositions
      final ImmutableSet<Proposition> sentenceProps = ImmutableSet.copyOf(st.propositions());
      // Filter down to good root propositions
      final ImmutableSet<Proposition> rootProps =
          FluentIterable.from(sentenceProps).filter(IsValidRootProposition.INSTANCE).toSet();

      // Count whether we had a valid root proposition
      rootPropCount += rootProps.size();
      if (rootProps.isEmpty()) {
        // Nothing more to do if there are no root propositions
        continue;
      } else {
        sentenceWithRootPropCount++;
      }

      // Filter down ActorMentions to the sentence
      final ImmutableSet<ActorMention> sentenceActorMentions =
          FluentIterable.from(docActorMentions)
              .filter(actorMentionMatchesSentence(dt, st))
              .toSet();

      // Filter down event mentions to the sentence
      final ImmutableSet<ICEWSEventMention> sentenceICEWSEvents =
          FluentIterable.from(eligibleICEWSEvents)
          .filter(ICEWSActors.icewsEventMentionMatchesSentence(dt, st))
          .toSet();

      generateEvents(sentenceActorMentions, sentenceICEWSEvents, st, dt, rootProps, sentenceProps);
    }
  }

  private void generateEvents(final ImmutableSet<ActorMention> sentenceActorMentions,
      final ImmutableSet<ICEWSEventMention> sentenceICEWSEvents, final SentenceTheory st, final DocTheory dt,
      final ImmutableSet<Proposition> rootProps, final ImmutableSet<Proposition> sentenceProps) {
    int sentenceICEWSMatched = 0;

    // Filter down the actor mentions to ones that we actually want
    final ImmutableSet<ActorMention> goodActorMentions = FluentIterable.from(sentenceActorMentions)
        .filter(Predicates.and(isProperOrCompositeActorMention(), ActorMentionFilter.EVENT_DISCOVERY))
        .toSet();

    // Map mentions to actor mentions. In ICEWS, unlike AWAKE, these are 1:1
    final BiMap<Mention, ActorMention> mentionActorMentions = ImmutableBiMap.copyOf(
        Maps.uniqueIndex(sentenceActorMentions, actorMentionMentionFunction()));

    // Filter ICEWS events to ones that only contain the good actor mentions
    final ImmutableSet<ICEWSEventMention> goodICEWSEvents = FluentIterable.from(sentenceICEWSEvents)
        .filter(icewsEventMentionOnlyContainsActorMentions(goodActorMentions))
        .toSet();
    icewsEligibleEventCount += goodICEWSEvents.size();

    // Make a map of the mention pairs to the corresponding (good) ICEWS events. If we're not
    // running on ACCENT output, this will be empty
    final ImmutableMultimap<MentionPair, ICEWSEventMention> mentionPairICEWSEvents =
        Multimaps.index(goodICEWSEvents, extractMentionPairFunction());
    // Make a mutable map to track any ICEWS events that we don't match. This starts with all of
    // them and is reduced every time one is matched.
    final Multimap<MentionPair, ICEWSEventMention> remainingMentionPairICEWSEvents =
        ArrayListMultimap.create(mentionPairICEWSEvents);

    // If running in ACCENT mode, we only want to consider ACCENT-coded mention pairs. Otherwise,
    // take all of them.
    final ImmutableSet<MentionPair> mentionPairs;
    switch (generationMethod) {
      case ACCENT:
        mentionPairs = mentionPairICEWSEvents.keySet();
        break;
      case WILD:
        // All combinations of mentions corresponding to actor mentions
        mentionPairs = pairActorMentions(goodActorMentions);
        break;
      default:
        throw new IllegalArgumentException(UNHANDLED_MSG);
    }

    // Make a map of of proposition references
    final ImmutableMap<OffsetRange<CharOffset>, Proposition> definitionalProps =
        PropositionUtils.mapDefinitionalPropositions(sentenceProps);

    // Dump the sentence propositions
    if (DEBUG_LOGGING) {
      System.out.println("**************************************");
      System.out.println(st.span().tokenizedText());
      System.out.println("Sentence propositions:");
      for (final Proposition prop : sentenceProps) {
        System.out.println(PropositionUtils.prettyPrintProposition(prop));
      }
      System.out.println();
    }

    // Create PropositionTree structures for the root props
    final ImmutableSet.Builder<PropositionTree> rootPropsTreeBuilder = ImmutableSet.builder();
    for (final Proposition prop : rootProps) {
      try {
        rootPropsTreeBuilder.add(PropositionTree.from(prop, definitionalProps));
      } catch (PropositionStructureException e) {
        log.warn("Exception when creating PropositionTree: {}", e.getMessage());
      }
    }
    final ImmutableSet<PropositionTree> rootPropTrees = rootPropsTreeBuilder.build();

    // Try to map each mention pair to the best proposition tree
    for (final MentionPair pair : mentionPairs) {
      // Find the first root proposition that covers it
      Optional<ExtractedPropositionTree> optCoveringTree = getCoveringPropInfo(pair, rootPropTrees,
          sentenceActorMentions);

      // Refine the proposition or exclude it if needed
      optCoveringTree = refineCoveringPropInfo(optCoveringTree);

      // Create an event if there is a covering proposition
      if (optCoveringTree.isPresent()) {
        final ExtractedPropositionTree extractedProp = optCoveringTree.get();
        // Get the matching ICEWS events
        final Collection<ICEWSEventMention> pairEvents = mentionPairICEWSEvents.get(pair);

        switch (generationMethod) {
          case ACCENT: {
            // Track the matched events
            for (final ICEWSEventMention event : pairEvents) {
              // Add a new event instance. Usage of getParticipant should be safe as we have already checked the
              // events we are iterating over
              final ExtractedPropositionTreeEvent eventInstance = ExtractedPropositionTreeEvent.create(
                  extractedProp.tree(), getParticipant(event, ROLE_SOURCE).actorMention(),
                  getParticipant(event, ROLE_TARGET).actorMention(), Optional.of(event), dt.docid(),
                  st.sentenceNumber(), extractedProp.hops(), st.tokenSequence().text());
              final ExtractedPropositionTreeEventInfo eventInfo =
                  ExtractedPropositionTreeEventInfo.fromEvent(eventInstance, extractedProp.filter());
              serializableEvents.add(eventInfo);
              generatedEvents++;
              if (DEBUG_LOGGING) {
                System.out.println("********************");
                System.out.println("Extracted ACCENT event:");
                System.out.println(st.tokenSpan().tokenizedText(dt));
                System.out.println(eventInfo.prettyPrint());
                System.out.println();
              }
            }

            icewsEligibleMatched += pairEvents.size();
            sentenceICEWSMatched += pairEvents.size();
            remainingMentionPairICEWSEvents.removeAll(pair);
            break;
          }
          case WILD: {
            // We don't know which ICEWS event is the best match, so we just take the first
            final Optional<ICEWSEventMention> icewsEvent = Optional.fromNullable(
                pairEvents.isEmpty()
                    ? null
                    : pairEvents.iterator().next());
            if (icewsEvent.isPresent()) {
              icewsEligibleMatched += pairEvents.size();
              sentenceICEWSMatched += pairEvents.size();
              remainingMentionPairICEWSEvents.removeAll(pair);
            }

            final ExtractedPropositionTreeEvent eventInstance = ExtractedPropositionTreeEvent.create(extractedProp.tree(),
                mentionActorMentions.get(pair.getFirstMention()), mentionActorMentions.get(pair.getSecondMention()),
                icewsEvent, dt.docid(), st.sentenceNumber(), extractedProp.hops(), st.tokenSequence().text());
            final ExtractedPropositionTreeEventInfo eventInfo =
                ExtractedPropositionTreeEventInfo.fromEvent(eventInstance, extractedProp.filter());
            serializableEvents.add(eventInfo);
            generatedEvents++;
            if (DEBUG_LOGGING) {
              System.out.println("********************");
              System.out.println("Extracted " + (icewsEvent.isPresent() ? "ACCENT" : "WILD")  +" event:");
              System.out.println(st.tokenSpan().tokenizedText(dt));
              System.out.println(eventInfo.prettyPrint());
              System.out.println();
            }
            break;
          }
          default:
            throw new IllegalArgumentException(UNHANDLED_MSG);
        }
      }
    }

    // Track the leftovers
    if (DEBUG_LOGGING) {
      if (sentenceICEWSMatched != goodICEWSEvents.size()) {
        System.out.format("Expected %d ICEWS events, matched %d\n", goodICEWSEvents.size(), sentenceICEWSMatched);
        System.out.println(st.tokenSpan().tokenizedText(dt));
        for (final MentionPair pair : remainingMentionPairICEWSEvents.keySet()) {
          System.out.println(pair.asString(dt));
          for (final ICEWSEventMention event : remainingMentionPairICEWSEvents.get(pair)) {
            System.out.println(event);
          }
        }
        for (final Proposition prop : sentenceProps) {
          System.out.println(PropositionUtils.prettyPrintProposition(prop));
        }
        System.out.println();
      }
    }
  }

  private Optional<ExtractedPropositionTree> refineCoveringPropInfo(
      final Optional<ExtractedPropositionTree> optTree) {
    // If absent, just return the same
    if (!optTree.isPresent()) {
      return optTree;
    }
    final ExtractedPropositionTree extractedProp = optTree.get();
    final PropositionTree tree = extractedProp.tree();

    // Filter out noun propositions for simple case
    if (PropositionPredicateType.NOUN.equals(tree.root().predType())) {
      // Create a new one with the filter set to ALL as it would not count under SIMPLE
      return Optional.of(ExtractedPropositionTree.create(tree, EventFilter.ALL, extractedProp.hops()));
    } else {
      // Return as-is
      return optTree;
    }
  }

  private ImmutableSet<MentionPair> pairActorMentions(final Set<ActorMention> actorMentions) {
    final ImmutableSet.Builder<MentionPair> ret = ImmutableSet.builder();
    // Use span equivalence to be sure we don't create a pair of "identical" mentions
    final Equivalence<Mention> mentionEquivalence = MentionSpanEquivalence.equivalence();
    for (final ActorMention am1 : actorMentions) {
      final Mention m1 = am1.mention();
      for (final ActorMention am2 : actorMentions) {
        final Mention m2 = am2.mention();
        // Skip (i, i) pairs and pairs where one mention contains the other
        if (mentionEquivalence.equivalent(m1, m2)
            || (m1.tokenSpan().contains(m2.tokenSpan()) || m2.tokenSpan().contains(m1.tokenSpan()))) {
          continue;
        }
        // Skip mentions of the same actor
        if (ActorType.getActorId(am1) == ActorType.getActorId(am2)) {
          continue;
        }

        ret.add(MentionPair.fromPreservingOrder(m1, m2));
      }
    }
    return ret.build();
  }

  private Optional<ExtractedPropositionTree> getCoveringPropInfo(final MentionPair mentionPair,
      final ImmutableSet<PropositionTree> trees,
      final ImmutableSet<ActorMention> sentenceActorMentions) {
    final Mention mention1 = mentionPair.getFirstMention();
    final Mention mention2 = mentionPair.getSecondMention();

    int bestHops = Integer.MAX_VALUE;
    ExtractedPropositionTree bestTree = null;
    for (final PropositionTree tree : trees) {
      // Get the path to each mention
      final Optional<PropositionTreePathFilter> optPath1 = tree.pathToMention(mention1,
          mentionsOfActorMentionsExcludingMention(sentenceActorMentions, mention1));
      final Optional<PropositionTreePathFilter> optPath2 = tree.pathToMention(mention2,
          mentionsOfActorMentionsExcludingMention(sentenceActorMentions, mention2));

      // Skip if one of the paths is missing
      if (!optPath1.isPresent() || !optPath2.isPresent()) {
        continue;
      }

      final PropositionTreePathFilter pathFilter1 = optPath1.get();
      final PropositionTreePathFilter pathFilter2 = optPath2.get();
      // Verify that the first proposition on the path is the same for both of them
      checkState(pathFilter1.root().equals(pathFilter2.root()),
          "Paths to mentions do not share the same root:\n" + pathFilter1.root() + "\n" +
              pathFilter2.root());

      // If either used ALL, that is the outcome
      final EventFilter filter =
          EventFilter.ALL.equals(pathFilter1.filter()) || EventFilter.ALL.equals(pathFilter2.filter())
              ? EventFilter.ALL
              : EventFilter.SIMPLE;

      // Compute hops
      int hops = pathFilter1.path().size() + pathFilter2.path().size();
      // We defend against this since miscomputed hops are difficult to debug and not worth
      // crashing over
      if (hops < 2) {
        log.error("Hops < 2 for paths {} and {}" + pathFilter1.path(), pathFilter2.path());
        hops = 2;
      }

      // Store if it's not above max hops and is the best so far
      if (hops <= maxHops && hops < bestHops) {
        bestTree = ExtractedPropositionTree.create(tree, filter, hops);
        bestHops = hops;
      }
    }

    return Optional.fromNullable(bestTree);
  }

  public ImmutableList<ExtractedPropositionTreeEventInfo> getSerializableEvents() {
    return serializableEvents.build();
  }

  @Override
  public void finish() {
    log.info("Documents processed: {}", documentCount);
    log.info("Sentences processed: {}", sentenceCount);
    log.info("Sentences with at least one root proposition: {}", sentenceWithRootPropCount);
    log.info("Root propositions: {}", rootPropCount);
    log.info("ICEWS events: {}", icewsEventCount);
    log.info("Eligible ICEWS events: {}", icewsEligibleEventCount);
    log.info("Matched eligible ICEWS events: {}", icewsEligibleMatched);
    log.info("Total events extracted: {}", generatedEvents);
  }

  private static ImmutableSet<MentionInfo> mentionsOfActorMentionsExcludingMention(
      final Iterable<ActorMention> actorMentions, final Mention mention) {
    return FluentIterable.from(actorMentions)
        .transform(TheoryUtils.actorMentionMentionFunction())
        .transform(MentionInfo.mentionInfoFromMentionFunction())
        .filter(Predicates.not(Predicates.equalTo(MentionInfo.from(mention))))
        .toSet();
  }

  public enum GenerationMethod {
    ACCENT,
    WILD
  }

  private enum IsValidRootProposition implements Predicate<Proposition> {
    INSTANCE;

    @Override
    public boolean apply(final Proposition input) {
      switch (PropositionPredicateType.fromPredicateType(input.predType())) {
        case NOUN:
          // We expect these to have a first argument that's a reference
          if (!input.args().isEmpty() && input.arg(0).roleIs(Proposition.Argument.REF_ROLE)
              && input.arg(0) instanceof MentionArgument) {
            final Mention mention = ((MentionArgument) input.arg(0)).mention();
            // Make sure that it is not an ACE entity by only accepting OTH role
            return ROOT_NOUN_ROLE.equalTo(mention.entityType().name());
          } else {
            log.warn("Noun proposition does not have expected structure");
            return false;
          }
        case VERB:
          return true;
        default:
          return false;
      }
    }
  }

  public static class ExtractedPropositionTree {
    private PropositionTree tree;
    private EventFilter filter;
    private int hops;

    private ExtractedPropositionTree(PropositionTree tree, EventFilter filter, int hops) {
      this.tree = tree;
      this.filter = filter;
      checkArgument(hops > 0);
      this.hops = hops;
    }

    public static ExtractedPropositionTree create(PropositionTree tree, EventFilter filter,
        int hops) {
      return new ExtractedPropositionTree(tree, filter, hops);
    }

    public PropositionTree tree() {
      return tree;
    }

    public EventFilter filter() {
      return filter;
    }

    public int hops() {
      return hops;
    }
  }

  public static class PropositionTreePathFilter {
    private PropositionNode root;
    private ImmutableList<PropositionEdge> path;
    private EventFilter filter;

    private PropositionTreePathFilter(PropositionNode root,
        ImmutableList<PropositionEdge> path, EventFilter filter) {
      this.root = root;
      this.path = path;
      this.filter = filter;
    }

    public static PropositionTreePathFilter create(final PropositionNode root,
        final ImmutableList<PropositionEdge> path, final EventFilter filter) {
      return new PropositionTreePathFilter(root, path, filter);
    }

    public PropositionNode root() {
      return root;
    }

    public ImmutableList<PropositionEdge> path() {
      return path;
    }

    public EventFilter filter() {
      return filter;
    }
  }
}
