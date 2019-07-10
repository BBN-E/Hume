package com.bbn.necd.event.icews;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.wrappers.ActorMentionPair;
import com.bbn.necd.event.wrappers.MentionPair;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.actors.ActorMention;
import com.bbn.serif.theories.actors.CompositeActorMention;
import com.bbn.serif.theories.actors.ProperNounActorMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention.ICEWSEventParticipant;

import com.google.common.annotations.Beta;
import com.google.common.base.Function;
import com.google.common.base.Optional;
import com.google.common.base.Predicate;
import com.google.common.base.Predicates;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;

import static com.google.common.base.Preconditions.checkArgument;

/**
 * Utility methods for working with ICEWS actors.
 */
@Beta
public final class ICEWSActors {

  public static final Symbol ROLE_SOURCE = Symbol.from("SOURCE");
  public static final Symbol ROLE_TARGET = Symbol.from("TARGET");

  private ICEWSActors() {
    throw new UnsupportedOperationException();
  }

  /**
   * A predicate which returns true if the {@link ActorMention} is a {@link ProperNounActorMention} or
   * {@link CompositeActorMention}.
   */
  public static Predicate<ActorMention> isProperOrCompositeActorMention() {
    return IsProperOrCompositeActorMention.INSTANCE;
  }

  /**
   * A predicate which returns true if the participant satisfies {@link #isProperOrCompositeActorMention()}.
   */
  public static Predicate<ICEWSEventParticipant> isProperOrCompositeICEWSEventParticipant() {
    return IsProperOrCompositeICEWSEventParticipant.INSTANCE;
  }

  /**
   * A predicate which returns true if the participant's role is SOURCE or TARGET.
   */
  public static Predicate<ICEWSEventParticipant> isTargetOrSourceICEWSEventParticipant() {
    return IsTargetOrSourceICEWSEventParticipant.INSTANCE;
  }

  /**
   * A predicate which returns true if a participant is a valid ICEWS event participant for the purposes of NECD,
   * namely one that satisfies {@link #isProperOrCompositeICEWSEventParticipant()} and
   * {@link #isTargetOrSourceICEWSEventParticipant}.
   */
  public static Predicate<ICEWSEventParticipant> isAcceptableICEWSEventParticipant() {
    return Predicates.and(isProperOrCompositeICEWSEventParticipant(), isTargetOrSourceICEWSEventParticipant());
  }

  /**
   * A predicate which returns true if an event mention has exactly two actors.
   */
  public static Predicate<ICEWSEventMention> isTwoActorICEWSEventMention() {
    return IsTwoActorICEWSEventMention.INSTANCE;
  }

  /**
   * A predicate which returns true if an event mention satisfies {@link #isTwoActorICEWSEventMention} and its
   * participants satisfy {@link #isAcceptableICEWSEventParticipant}.
   */
  public static Predicate<ICEWSEventMention> isAcceptableICEWSEventMention() {
    return IsAcceptableICEWSEventMention.INSTANCE;
  }

  /**
   * Create a {@link MentionPair} from a two-participant {@link ICEWSEventMention}, preserving the mention order. Will
   * raise an error if the specified event mention does not have exactly two participants.
   *
   * @param eventMention the event mention to extract participants from
   * @return a mention pair from the two participants of the event mention
   */
  public static MentionPair eventMentionPair(final ICEWSEventMention eventMention) {
    checkArgument(eventMention.numEventParticipants() == 2);
    final ImmutableList<ICEWSEventParticipant> participants = eventMention.eventParticipants();
    return MentionPair.fromPreservingOrder(participants.get(0).actorMention().mention(),
        participants.get(1).actorMention().mention());
  }

  public static ActorMentionPair eventActorMentionPair(final ICEWSEventMention eventMention) {
    checkArgument(eventMention.numEventParticipants() == 2);
    final ImmutableList<ICEWSEventParticipant> participants = eventMention.eventParticipants();
    return ActorMentionPair.from(participants.get(0).actorMention(),
        participants.get(1).actorMention());
  }

  // TODO: Document
  public static ImmutableList<MentionPair> allMentionPairs(final Iterable<Mention> mentions) {
    final ImmutableList.Builder<MentionPair> ret = ImmutableList.builder();

    // Create all non-duplicate mention pairs
    for (final Mention m1 : mentions) {
      for (final Mention m2 : mentions) {
        if (m1.equals(m2)) {
          continue;
        }
        ret.add(MentionPair.fromPreservingOrder(m1, m2));
      }
    }

    return ret.build();
  }

  // TODO: Document
  // Functionally equivalent to #allMentionPairs, but cannot have same method name due to type erasure.
  public static ImmutableList<MentionPair> allActorMentionPairs(final Iterable<ActorMention> actorMentions) {
    // Collect the mentions
    final ImmutableList.Builder<Mention> mentionBuilder = ImmutableList.builder();
    for (final ActorMention am : actorMentions) {
      mentionBuilder.add(am.mention());
    }
    return allMentionPairs(mentionBuilder.build());
  }

    /**
     * A function that applies {@link #eventMentionPair}.
     */
  public static Function<ICEWSEventMention, MentionPair> extractMentionPairFunction() {
    return ExtractMentionPairFunction.INSTANCE;
  }

  public static Function<ICEWSEventMention, ActorMentionPair> extractActorMentionPairFunction() {
    return ExtractActorMentionPairFunction.INSTANCE;
  }

  /**
   * A predicate that returns whether an {@link ICEWSEventMention}'s {@link SentenceTheory} matches the specified
   * {@link SentenceTheory}.
   *
   * @param docTheory the document theory to test against
   * @param sentenceTheory the sentence theory to test against
   * @return the predicate
   */
  public static Predicate<ICEWSEventMention> icewsEventMentionMatchesSentence(final DocTheory docTheory,
      final SentenceTheory sentenceTheory) {
    return new ICEWSEventMentionMatchesSentence(docTheory, sentenceTheory);
  }

  /**
   * A predicate that returns whether all of an {@link ICEWSEventMention}'s {@link ActorMention}s
   * are contained within the specified set of {@link ActorMention}s.
   *
   * @param actorMentions the set of actor mentions to test against
   * @return the predicate
   */
  public static Predicate<ICEWSEventMention> icewsEventMentionOnlyContainsActorMentions(
      final ImmutableSet<ActorMention> actorMentions) {
    return new ICEWSEventMentionOnlyContainsActorMentions(actorMentions);
  }

  // TODO: Document
  public static ICEWSEventParticipant getParticipant(final ICEWSEventMention eventMention, final Symbol role) {
    final Optional<ICEWSEventParticipant> participant = eventMention.eventParticipantForRole(role);
    checkArgument(participant.isPresent(), "Event mention must have a " + role.asString() + " participant");
    return participant.get();
  }

  // TODO: Document or delete
  public static String prettyPrintICEWSEventMention(final ICEWSEventMention eventMention) {
    final StringBuilder sb = new StringBuilder(eventMention.code().toString());
    sb.append(": ");
    boolean first = true;
    for (final ICEWSEventParticipant participant : eventMention.eventParticipants()) {
      if (!first) {
        sb.append(", ");
      } else {
        first = false;
      }

      sb.append(participant.actorMention().mention().head().terminalSymbols().toString());
    }

    return sb.toString();
  }

  private enum IsProperOrCompositeActorMention implements Predicate<ActorMention> {
    INSTANCE;

    @Override
    public boolean apply(final ActorMention actorMention) {
      return (actorMention instanceof ProperNounActorMention) || (actorMention instanceof CompositeActorMention);
    }
  }

  /**
   * A representation of the roles of an ICEWS actor.
   */
  public enum Role {
    SOURCE,
    TARGET,
    OTHER;

    /**
     * Return the role value associated with the specified role
     * @param role the role
     * @return the enum value
     */
    public Role fromSymbol(final Symbol role) {
      if (role.equalTo(ROLE_SOURCE)) {
        return SOURCE;
      } else if (role.equalTo(ROLE_TARGET)) {
        return TARGET;
      } else {
        return OTHER;
      }
    }
  }

  private enum IsProperOrCompositeICEWSEventParticipant implements Predicate<ICEWSEventParticipant> {
    INSTANCE;

    @Override
    public boolean apply(final ICEWSEventParticipant eventParticipant) {
      return IsProperOrCompositeActorMention.INSTANCE.apply(eventParticipant.actorMention());
    }
  }

  private enum IsTargetOrSourceICEWSEventParticipant implements Predicate<ICEWSEventParticipant> {
    INSTANCE;

    @Override
    public boolean apply(final ICEWSEventParticipant eventParticipant) {
      return (eventParticipant.role().equalTo(ROLE_SOURCE) || eventParticipant.role().equalTo(ROLE_TARGET));
    }
  }

  private enum IsTwoActorICEWSEventMention implements Predicate<ICEWSEventMention> {
    INSTANCE;

    @Override
    public boolean apply(final ICEWSEventMention input) {
      return input.numEventParticipants() == 2;
    }
  }

  private enum IsAcceptableICEWSEventMention implements Predicate<ICEWSEventMention> {
    INSTANCE;

    @Override
    public boolean apply(final ICEWSEventMention input) {
      // Check that it is a two-participant event mention and that both participants are what we want
      return isTwoActorICEWSEventMention().apply(input)
          && isAcceptableICEWSEventParticipant().apply(input.eventParticipants().get(0))
          && isAcceptableICEWSEventParticipant().apply(input.eventParticipants().get(1));
    }
  }

  private enum ExtractMentionPairFunction implements Function<ICEWSEventMention, MentionPair> {
    INSTANCE;

    @Override
    public MentionPair apply(final ICEWSEventMention input) {
      return eventMentionPair(input);
    }
  }

  private enum ExtractActorMentionPairFunction implements Function<ICEWSEventMention, ActorMentionPair> {
    INSTANCE;

    @Override
    public ActorMentionPair apply(final ICEWSEventMention input) {
      return eventActorMentionPair(input);
    }
  }

  private static class ICEWSEventMentionMatchesSentence implements Predicate<ICEWSEventMention> {

    private final DocTheory docTheory;
    private final SentenceTheory sentenceTheory;

    private ICEWSEventMentionMatchesSentence(final DocTheory docTheory, final SentenceTheory sentenceTheory) {
      this.docTheory = docTheory;
      this.sentenceTheory = sentenceTheory;
    }

    @Override
    public boolean apply(final com.bbn.serif.theories.icewseventmentions.ICEWSEventMention input) {
      checkArgument(input.numEventParticipants() > 0);
      // We check by making sure the first participant belongs in this sentence.
      // This will fall back on object equality, which is fine
      return input.eventParticipants().get(0).actorMention().mention().sentenceTheory(docTheory).equals(sentenceTheory);
    }
  }

  private static class ICEWSEventMentionOnlyContainsActorMentions implements Predicate<ICEWSEventMention> {

    private final ImmutableSet<ActorMention> actorMentions;

    private ICEWSEventMentionOnlyContainsActorMentions(final ImmutableSet<ActorMention> actorMentions) {
      this.actorMentions = actorMentions;
    }

    @Override
    public boolean apply(final ICEWSEventMention input) {
      checkArgument(input.numEventParticipants() > 0);
      for (final ICEWSEventParticipant participant : input.eventParticipants()) {
        // If the actor mention isn't in the set, return false
        if (!actorMentions.contains(participant.actorMention())) {
          return false;
        }
      }
      // If all were found, return true
      return true;
    }
  }
}
