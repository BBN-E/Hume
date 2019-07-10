package com.bbn.necd.event.icews;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.wrappers.ICEWSEventMentionInfo;
import com.bbn.necd.event.wrappers.MentionSpanEquivalence;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.actors.ActorMention;
import com.bbn.serif.theories.actors.SimpleActorMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention.ICEWSEventParticipant;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMentions;
import com.google.common.base.Equivalence;
import com.google.common.base.Function;
import com.google.common.base.Optional;
import com.google.common.collect.HashBasedTable;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Table;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.List;

import static com.bbn.necd.event.icews.ICEWSActors.isTwoActorICEWSEventMention;

public final class ICEWSEventInstanceGenerator implements Function<DocTheory, ImmutableList<ICEWSEventInstance>> {

  private static final Logger log = LoggerFactory.getLogger(ICEWSEventInstanceGenerator.class);

  private int allIcewsEventsObserved = 0;
  private int twoArgIcewsEventsObserved = 0;
  private int simpleArgEventInstances = 0;

  private ICEWSEventInstanceGenerator() {
  }

  public static ICEWSEventInstanceGenerator from(final Parameters params) throws IOException {
    return new ICEWSEventInstanceGenerator();
  }

  public int getAllIcewsEventsObserved() {
    return allIcewsEventsObserved;
  }

  public int getTwoArgIcewsEventsObserved() {
    return twoArgIcewsEventsObserved;
  }

  private static Optional<Symbol> getICEWSRole(final ICEWSEventMention em, final Mention mention) {
    for (final ICEWSEventParticipant participant : em.eventParticipants()) {
      if (participant.actorMention().mention().span().equals(mention.span())) {
        return Optional.of(participant.role());
      }
    }
    return Optional.absent();
  }

  private static ImmutableSet<Mention> getPropositionArgumentMentions(final Proposition prop) {
    final ImmutableSet.Builder<Mention> ret = ImmutableSet.builder();

    for (final Proposition.Argument propArg : prop.args()) {
      if (propArg instanceof Proposition.MentionArgument) {
        final Proposition.MentionArgument mentionArg = (Proposition.MentionArgument) propArg;
        ret.add(mentionArg.mention());
      }
    }
    return ret.build();
  }

  private static Optional<ActorMention> getICEWSActorMention(final ICEWSEventMention icewsEventMention,
      final Mention mention) {
    final Equivalence.Wrapper<Mention> wrappedMention = wrapMention(mention);
    for (final ICEWSEventParticipant part : icewsEventMention.eventParticipants()) {
      final ActorMention actorMention = part.actorMention();
      if (wrappedMention.equals(wrapMention(actorMention.mention()))) {
        return Optional.of(actorMention);
      }
    }
    return Optional.absent();
  }

  private static Equivalence.Wrapper<Mention> wrapMention(final Mention mention) {
    return MentionSpanEquivalence.wrap(mention);
  }

  @Override
  public ImmutableList<ICEWSEventInstance> apply(final DocTheory dt) {
    final ImmutableList.Builder<ICEWSEventInstance> ret = ImmutableList.builder();

    // Filter down to two actor events
    final ICEWSEventMentions allMentions = dt.icewsEventMentions();
    allIcewsEventsObserved += allMentions.size();
    final ImmutableList<ICEWSEventMention> icewsEventMentions = ImmutableList.copyOf(
        Iterables.filter(allMentions, isTwoActorICEWSEventMention()));
    twoArgIcewsEventsObserved += icewsEventMentions.size();

    // Map the mentions for the participants to the ICEWS event mentions
    final Table<Equivalence.Wrapper<Mention>, Equivalence.Wrapper<Mention>, ICEWSEventMention> icewsEventsByMentions =
        makeICEWSEventMentionTable(icewsEventMentions);

    // Find propositions that match the ICEWS event mentions
    for (final SentenceTheory st : dt.nonEmptySentenceTheories()) {
      for (final Proposition prop : st.propositions()) {
        if (prop.predType().isVerbal() && prop.predHead().isPresent()) {
          final ImmutableSet<Mention> propMentions = getPropositionArgumentMentions(prop);
          if (propMentions.size() >= 2) {
            // Generate an event instance if we can
            final List<ICEWSEventInstance> eventInstances = makeEventInstance(prop, propMentions,
                icewsEventsByMentions);
            ret.addAll(eventInstances);
          }
        }
      }
    }
    return ret.build();
  }

  private static Table<Equivalence.Wrapper<Mention>, Equivalence.Wrapper<Mention>, ICEWSEventMention> makeICEWSEventMentionTable(
      final Iterable<ICEWSEventMention> icewsEventMentions) {
    // The use of MentionWrapper is to get around the fact that mention doesn't implement equals
    final Table<Equivalence.Wrapper<Mention>, Equivalence.Wrapper<Mention>, ICEWSEventMention> icewsEventsByMentions =
        HashBasedTable.create();
    for (final ICEWSEventMention event : icewsEventMentions) {
      final ImmutableList<ICEWSEventParticipant> participants = event.eventParticipants();
      final ICEWSEventParticipant part1 = participants.get(0);
      final ICEWSEventParticipant part2 = participants.get(1);
      icewsEventsByMentions.put(wrapMention(part1.actorMention().mention()),
          wrapMention(part2.actorMention().mention()), event);
    }
    return icewsEventsByMentions;
  }

  private static ImmutableList<ICEWSEventInstance> makeEventInstance(final Proposition prop,
      final Iterable<Mention> propMentions,
      final Table<Equivalence.Wrapper<Mention>, Equivalence.Wrapper<Mention>, ICEWSEventMention> icewsEventsByMentions) {
    final ImmutableList.Builder<ICEWSEventInstance> ret = ImmutableList.builder();
    // Search through the combinations of mentions from this proposition to try to find one that
    // matches the ICEWS events
    for (final Mention mention1 : propMentions) {
      final Equivalence.Wrapper<Mention> wrappedMention1 = wrapMention(mention1);
      for (final Mention mention2 : propMentions) {
        final Equivalence.Wrapper<Mention> wrappedMention2 = wrapMention(mention2);
        // Skip identical mentions
        if (wrappedMention1.equals(wrappedMention2)) {
          continue;
        }

        // Try to find in the icews event mention. If the order is mention2, mention1, we'll get
        // it in another iteration.
        final ICEWSEventMention icewsEventMention =
            icewsEventsByMentions.get(wrappedMention1, wrappedMention2);
        if (icewsEventMention == null) {
          // Nothing more to do since there was no ICEWS event to match up with
          continue;
        }

        final ICEWSEventMentionInfo icewsEventMentionInfo =
            ICEWSEventMentionInfo.fromICEWSEventMention(icewsEventMention);

        // These gets do not fail under any known conditions
        final Optional<Symbol> actor1Role = getICEWSRole(icewsEventMention, mention1);
        final Optional<Symbol> actor2Role = getICEWSRole(icewsEventMention, mention2);
        final Optional<ActorMention> actorMention1 =
            getICEWSActorMention(icewsEventMention, mention1);
        final Optional<ActorMention> actorMention2 =
            getICEWSActorMention(icewsEventMention, mention2);

        if (actorMention1.get() instanceof SimpleActorMention
            || actorMention2.get() instanceof SimpleActorMention) {
          // These don't have actor IDs so they need to be skipped
          continue;
        }

        // Add event if everything is present and the right types
        if (actor1Role.isPresent() && actor2Role.isPresent()
            && actorMention1.isPresent() && actorMention2.isPresent()) {

          final ICEWSEventInstance eventInstance = ICEWSEventInstance.builder(prop)
              .withArgument(ICEWSEventInstance.Argument.from(actorMention1.get(), actor1Role.get()))
              .withArgument(ICEWSEventInstance.Argument.from(actorMention2.get(), actor2Role.get()))
              .withICEWSEventMentionInfo(icewsEventMentionInfo)
              .build();

          ret.add(eventInstance);
        } else {
          log.info("Actor roles or mentions missing in event mention {}", icewsEventMention);
        }
      }
    }
    return ret.build();
  }
}
