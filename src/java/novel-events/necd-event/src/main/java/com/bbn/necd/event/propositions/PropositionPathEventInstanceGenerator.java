package com.bbn.necd.event.propositions;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PropositionUtils;
import com.bbn.necd.common.theory.PropositionGraph;
import com.bbn.necd.common.theory.PropositionPath;
import com.bbn.necd.event.icews.ICEWSActors;
import com.bbn.necd.event.wrappers.ICEWSEventMentionInfo;
import com.bbn.necd.event.wrappers.MentionPair;
import com.bbn.necd.event.wrappers.MentionSpanEquivalence;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.actors.ActorMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention.ICEWSEventParticipant;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMentions;

import com.google.common.base.Equivalence;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.Collection;
import java.util.Map;
import java.util.Set;

public final class PropositionPathEventInstanceGenerator {

  // TODO: Remove this constant once things are stable.
  private static final boolean DEBUG_LOGGING = false;

  // Example of path length 2: barak_<sub>_met_<with>_yosef
  // Example of path length 3: florida_<from>_flew_<into>_airspace_<unknown>_cuban
  private static final int MAX_PATH_LENGTH = 99;

  private static final Logger log = LoggerFactory.getLogger(PropositionPathEventInstanceGenerator.class);

  private int icewsEventMentionCount;
  private int icewsEventMentionMatch;

  private final ImmutableList.Builder<String> missRecords;
  private final ImmutableList.Builder<String> multiRecords;

  private final ImmutableList.Builder<PropositionPathEventInstance> events;

  private PropositionPathEventInstanceGenerator() {
    missRecords = ImmutableList.builder();
    multiRecords = ImmutableList.builder();
    events = ImmutableList.builder();
  }

  public static PropositionPathEventInstanceGenerator from(final Parameters params) {
    return new PropositionPathEventInstanceGenerator();
  }

  public ImmutableList<String> getMissRecords() {
    return missRecords.build();
  }

  public ImmutableList<String> getMultiRecords() {
    return multiRecords.build();
  }

  public void process(DocTheory dt) {
    // All pairs of Mention (from ActorMention) which are:
    // (i)  connected by proposition path of max length MAX_PATH_LENGTH
    // (ii) satisfies Predicate isProperOrCompositeActorMention
    final ImmutableMultimap<MentionPair, PropositionPath> allCandidates = getAllEventInstanceCandidates(dt);

    // All pairs of ActorMention which are:
    // (i)  participants in the mapped ICEWSEventMention (we use Multimap to allow possibility of a pair being involved in more than one ICEWS event
    // (ii) satisfies Predicate ProperOrCompositeICEWSEventParticipant
    final ImmutableMultimap<MentionPair, ICEWSEventMention> allICEWSEventParticipantPairs = getAllICEWSEventParticipantPairs(dt.icewsEventMentions());
    icewsEventMentionCount += allICEWSEventParticipantPairs.size();
    //final ImmutableMap<MentionPair, ICEWSEventMention> filteredICEWSEventParticipantPairs = filterICEWSEventParticipantPairs(allICEWSEventParticipantPairs);
    //icewsEventMentionCount += filteredICEWSEventParticipantPairs.size();

    // These will form our training data
    final ImmutableSet<MentionPair> candidatesMappableToICEWSEvent = Sets.intersection(allCandidates.keySet(), allICEWSEventParticipantPairs.keySet()).immutableCopy();
    //log.info("candidatesMappableToICEWSEvent size={}", candidatesMappableToICEWSEvent.size());
    //icewsEventMentionMatch += candidatesMappableToICEWSEvent.size();
    for(final MentionPair pair : candidatesMappableToICEWSEvent) {
      icewsEventMentionMatch += allICEWSEventParticipantPairs.get(pair).size();
    }

    // Since the Predicates ProperOrCompositeActorMention and ProperOrCompositeICEWSEventParticipant are essentially the same, only misses should be caused by:
    // (i)  We cannot find a proposition path between the ActorMention pair, or we found a path that is longer than length threshold maxPathLength
    // (ii) Participants from the same ICEWSEventMention can be from different sentences?
    final ImmutableSet<MentionPair> icewsEventsMissedByCandidates = Sets.difference(allICEWSEventParticipantPairs.keySet(), allCandidates.keySet()).immutableCopy();
    for (final MentionPair pair : icewsEventsMissedByCandidates) {
      final StringBuilder sb = new StringBuilder(dt.docid().asString());
      sb.append(" ");
      sb.append(mentionIndicesAsString(pair.getFirstMention()));
      sb.append(" ");
      sb.append(mentionIndicesAsString(pair.getSecondMention()));
      sb.append(" ");
      for(final ICEWSEventMention em : allICEWSEventParticipantPairs.get(pair)) {
        sb.append(" " + em.patternId());
      }
      missRecords.add(sb.toString());
    }

    multiRecords.addAll(logMentionPairToMultiICEWSEventMention(dt, allICEWSEventParticipantPairs));

    // ICEWS is better at precision than recall. These are its potential recall misses
    final ImmutableSet<MentionPair> potentialRecallMissesByICEWS = Sets.difference(allCandidates.keySet(), allICEWSEventParticipantPairs.keySet()).immutableCopy();

    events.addAll(toEventInstances(allCandidates, allICEWSEventParticipantPairs, dt));
  }

  private ImmutableMap<MentionPair, ICEWSEventMention> filterICEWSEventParticipantPairs(
      final ImmutableMultimap<MentionPair, ICEWSEventMention> allICEWSEventParticipantPairs) {
    final ImmutableMap.Builder<MentionPair, ICEWSEventMention> ret = ImmutableMap.builder();

    for (final Map.Entry<MentionPair, Collection<ICEWSEventMention>> entry : allICEWSEventParticipantPairs.asMap().entrySet()) {
      if (entry.getValue().size() == 1) {
        ret.put(entry.getKey(), ImmutableList.copyOf(entry.getValue()).get(0));
      }
    }

    return ret.build();
  }

  // look at instances where the same Mention pair maps to multiple ICEWS event mention
  private ImmutableList<String> logMentionPairToMultiICEWSEventMention(final DocTheory dt, final ImmutableMultimap<MentionPair, ICEWSEventMention> allICEWSEventParticipantPairs) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    for (final Map.Entry<MentionPair, Collection<ICEWSEventMention>> entry : allICEWSEventParticipantPairs.asMap().entrySet()) {
      final MentionPair pair = entry.getKey();
      final Collection<ICEWSEventMention> eventMentions = entry.getValue();
      if (eventMentions.size() > 1) {
        final StringBuilder s = new StringBuilder(dt.docid().asString());
        s.append(" ");
        s.append(mentionIndicesAsString(pair.getFirstMention()));
        s.append(" ");
        s.append(mentionIndicesAsString(pair.getSecondMention()));
        Set<Symbol> eventCodes = Sets.newHashSet();
        for (final ICEWSEventMention em : eventMentions) {
          s.append(" ||| ");
          s.append(em.code().toString() + ":" + em.patternId());
          eventCodes.add(em.code());

          s.append(" " + em.numEventParticipants());
          for(int i=0; i<em.numEventParticipants(); i++) {
            s.append(" " + em.eventParticipant(i).role() + ":" + mentionIndicesAsString(em.eventParticipant(i).actorMention().mention()));
          }
        }
        s.append(" ");
        s.append(eventCodes.size());
        ret.add(s.toString());
      }
    }

    return ret.build();
  }

  private ImmutableList<PropositionPathEventInstance> toEventInstances(final ImmutableMultimap<MentionPair, PropositionPath> allCandidates,
      final ImmutableMultimap<MentionPair, ICEWSEventMention> ICEWSEventParticipantPairs, final DocTheory dt) {
    final ImmutableList.Builder<PropositionPathEventInstance> ret = ImmutableList.builder();

    // we will use this to create event instances for now, since we haven't decided how to sample the candidates not found by ICEWS
    final ImmutableSet<MentionPair> candidatesMappableToICEWSEvent = Sets.intersection(allCandidates.keySet(), ICEWSEventParticipantPairs.keySet()).immutableCopy();

    for (final MentionPair pair : candidatesMappableToICEWSEvent) {
      final Mention m1 = pair.getFirstMention();
      final Mention m2 = pair.getSecondMention();
      final PropositionPath path = allCandidates.get(pair).asList().get(0);  // TODO: currently, we will only get 1 path.

      for (final ICEWSEventMention em : ICEWSEventParticipantPairs.get(pair)) {
        final ImmutableList<ICEWSEventParticipant> participants = ImmutableList.copyOf(
            Iterables
                .filter(em.eventParticipants(), ICEWSActors.isAcceptableICEWSEventParticipant()));

        if (participants.size() == 2) {
          final ICEWSEventParticipant participant1 = participants.get(0);
          final ICEWSEventParticipant participant2 = participants.get(1);

          if (participant1.actorMention().mention() == m1
              && participant2.actorMention().mention() == m2) {
            final ICEWSEventMentionInfo emInfo =
                ICEWSEventMentionInfo.from(em.code(), em.tense(), em.patternId());
            ret.add(
                PropositionPathEventInstance.builder(m1, m2, path).withICEWSEventMentionInfo(emInfo)
                    .build());

          } else if (participant1.actorMention().mention() == m2
              && participant2.actorMention().mention() == m1) {
            final ICEWSEventMentionInfo emInfo =
                ICEWSEventMentionInfo.from(em.code(), em.tense(), em.patternId());
            ret.add(
                PropositionPathEventInstance.builder(m1, m2, path).withICEWSEventMentionInfo(emInfo)
                    .build());

          } else {
            log.info("ERROR: participants do not match mentions");
          }
        } else {
          log.error("ERROR, participants size not 2. This shouldn't happen");
        }
      }
    }

    final ImmutableList<PropositionPathEventInstance> eventInstances = ret.build();
    if (DEBUG_LOGGING && !eventInstances.isEmpty()) {
      for (final PropositionPathEventInstance eventInstance : eventInstances) {
        System.out.println(eventInstance.getPropositionPath().getSentenceTheory().tokenSequence().tokenSpan().tokenizedText(dt));
        final Optional<String> optPath = eventInstance.getPropositionPath().pathAsString();
        if (optPath.isPresent()) {
          System.out.println(optPath.get());
        } else {
          System.out.println("Path is absent");
        }
        System.out.println();
      }
    }

    return eventInstances;
  }

  private ImmutableMultimap<MentionPair, ICEWSEventMention> getAllICEWSEventParticipantPairs(final ICEWSEventMentions icewsEventMentions) {
    final ImmutableMultimap.Builder<MentionPair, ICEWSEventMention> ret = ImmutableMultimap.builder();

    for (final ICEWSEventMention em : icewsEventMentions) {
      final ImmutableList<ICEWSEventParticipant> participants = ImmutableList.copyOf(
          Iterables.filter(em.eventParticipants(), ICEWSActors.isAcceptableICEWSEventParticipant()));
      final ImmutableSet<Equivalence.Wrapper<Mention>> mentions = participantToMentionWrapperSet(participants);

      if (participants.size() == 2 && mentions.size() == 2) {
        final ImmutableList<Equivalence.Wrapper<Mention>> mentionList = ImmutableList.copyOf(mentions);
        final MentionPair pair = MentionPair.fromIgnoringOrder(mentionList.get(0), mentionList.get(1));
        ret.put(pair, em);
      }
    }

    return ret.build();
  }

  private ImmutableMultimap<MentionPair, PropositionPath> getAllEventInstanceCandidates(final DocTheory dt) {
    final ImmutableMultimap.Builder<MentionPair, PropositionPath> ret = ImmutableMultimap.builder();

    final ImmutableList<ActorMention> actors = ImmutableList.copyOf(Iterables.filter(dt.actorMentions(),
        ICEWSActors.isProperOrCompositeActorMention()));
    final ImmutableSet<Equivalence.Wrapper<Mention>> mentions = actorToMentionWrapperSet(actors);

    // organize the mentions by sentence
    final ImmutableMultimap.Builder<SentenceTheory, Equivalence.Wrapper<Mention>> mentionsBySentenceBuilder = ImmutableMultimap.builder();
    for (final Equivalence.Wrapper<Mention> mentionWrapper : mentions) {
      mentionsBySentenceBuilder.put(mentionWrapper.get().sentenceTheory(dt), mentionWrapper);
    }
    final ImmutableMultimap<SentenceTheory, Equivalence.Wrapper<Mention>> mentionsBySentence = mentionsBySentenceBuilder.build();

    for (final SentenceTheory st : mentionsBySentence.keySet()) {
      ret.putAll(getAllEventInstanceCandidates(st, ImmutableSet.copyOf(mentionsBySentence.get(st))));
    }

    return ret.build();
  }

  // we are actually interested in pair of ActorMention to PropositionPath, but there is a one-to-many relationship from Mention to ActorMention
  private ImmutableMultimap<MentionPair, PropositionPath> getAllEventInstanceCandidates(final SentenceTheory st,
      final ImmutableSet<Equivalence.Wrapper<Mention>> mentions) {
    final ImmutableMultimap.Builder<MentionPair, PropositionPath> ret = ImmutableMultimap.builder();

    if (mentions.size() >= 2) {
      final PropositionGraph propositionGraph = PropositionGraph.from(st);

      // TODO: multimap allows for the possibility of multiple paths between a pair of actors (though this isn't implemented yet)
      // PropositionGraph.findPropPath(final PathNode source, final PathNode target) would have to return multiple paths
      ret.putAll(getPathBetweenMentions(mentions, propositionGraph));
    }

    return ret.build();
  }


  private ImmutableMultimap<MentionPair, PropositionPath> getPathBetweenMentions(
      final ImmutableSet<Equivalence.Wrapper<Mention>> mentions, final PropositionGraph propositionGraph) {
    final ImmutableMultimap.Builder<MentionPair, PropositionPath> ret = ImmutableMultimap.builder();
    Set<MentionPair> seenMentionWrapperPairs = Sets.newHashSet();

    for (final Equivalence.Wrapper<Mention> mention1 : mentions) {
      for (final Equivalence.Wrapper<Mention> mention2 : mentions) {
        if (!mention1.equals(mention2)) {
          final MentionPair pair = MentionPair.fromIgnoringOrder(mention1, mention2);
          if (!seenMentionWrapperPairs.contains(pair)) {
            seenMentionWrapperPairs.add(pair);

            final Optional<PropositionPath> path = propositionGraph.getPropPath(PropositionUtils.getTerminalHead(pair.getFirstMention()),
                PropositionUtils.getTerminalHead(pair.getSecondMention()));

            if (path.isPresent() && path.get().length() <= MAX_PATH_LENGTH) {
              ret.put(pair, path.get());
            } else {
              if (path.isPresent()) {
                log.info("Path length {} too long for {} {}", path.get().length(),
                    mentionIndicesAsString(pair.getFirstMention()), mentionIndicesAsString(pair.getSecondMention()));
              }
            }
          }
        }
      }
    }

    return ret.build();
  }

  private ImmutableSet<Equivalence.Wrapper<Mention>> actorToMentionWrapperSet(final Iterable<ActorMention> actorMentions) {
    final ImmutableSet.Builder<Equivalence.Wrapper<Mention>> ret = ImmutableSet.builder();

    for (final ActorMention actorMention : actorMentions) {
      ret.add(MentionSpanEquivalence.wrap(actorMention.mention()));
    }

    return ret.build();
  }

  private ImmutableSet<Equivalence.Wrapper<Mention>> participantToMentionWrapperSet(final Iterable<ICEWSEventParticipant> participants) {
    final ImmutableSet.Builder<Equivalence.Wrapper<Mention>> ret = ImmutableSet.builder();

    for (final ICEWSEventParticipant participant : participants) {
      ret.add(MentionSpanEquivalence.wrap(participant.actorMention().mention()));
    }

    return ret.build();
  }

  private static String mentionIndicesAsString(final Mention m) {
    return m.sentenceNumber() + ":" + m.span().startIndex() + "-" + m.span().endIndex() + ":" + m.span().startCharOffset().asInt() + "-" + m.span().endCharOffset().asInt();
  }

  public ImmutableList<PropositionPathEventInstance> getSerializableEvents() {
    return events.build();
  }

  public void logStatistics() {
    log.info("icewsEventMentionCount = {}", icewsEventMentionCount);
    log.info("icewsEventMentionMatch = {}", icewsEventMentionMatch);
  }

  public void writeMissRecords(final File file) {
    // Do nothing
  }

  public ImmutableList<PropositionPathEventInstance> getGeneratedEvents() {
    return events.build();
  }

}
