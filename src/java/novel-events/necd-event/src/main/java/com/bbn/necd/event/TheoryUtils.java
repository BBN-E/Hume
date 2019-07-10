package com.bbn.necd.event;

import com.bbn.bue.common.EquivalenceUtils;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.wrappers.MentionSpanEquivalence;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.TokenSequence;
import com.bbn.serif.theories.actors.ActorMention;
import com.google.common.annotations.Beta;
import com.google.common.base.Equivalence;
import com.google.common.base.Function;
import com.google.common.base.Predicate;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Utilities to make it easier to work with various JSerif theory classes.
 */
@Beta
public final class TheoryUtils {

  /**
   * A predicate that returns whether an {@link ActorMention}'s {@link Mention} is contained in a specified set of
   * {@link Mention}s.
   */
  public static Predicate<ActorMention> actorMentionMatchesMentions(final Iterable<Mention> mentions) {
    return new ActorMentionMatchesMentions(mentions);
  }

  /**
   * A predicate that returns whether an {@link ActorMention}'s {@link SentenceTheory} matches the specified
   * {@link SentenceTheory}.
   */
  public static Predicate<ActorMention> actorMentionMatchesSentence(final DocTheory docTheory,
      final SentenceTheory sentenceTheory) {
    return new ActorMentionMatchesSentence(docTheory, sentenceTheory);
  }

  /**
   * A function that maps a {@link ActorMention} to its corresponding {@link Mention}.
   */
  public static Function<ActorMention, Mention> actorMentionMentionFunction() {
    return ActorMentionToMentionFunction.INSTANCE;
  }

  /**
   * Returns the tokens corresponding to a mention.
   */
  public static ImmutableList<Symbol> mentionTokens(final Mention mention) {
    final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();
    final TokenSequence.Span span = mention.span();
    final TokenSequence tokenSequence = span.tokenSequence();
    final int start = span.startTokenIndexInclusive();
    final int end = span.endTokenIndexInclusive();
    for (int i = start; i <= end; i++) {
      ret.add(tokenSequence.token(i).symbol());
    }
    return ret.build();
  }

  private static class ActorMentionMatchesMentions implements Predicate<ActorMention> {

    private final ImmutableSet<Equivalence.Wrapper<Mention>> mentions;

    private ActorMentionMatchesMentions(final Iterable<Mention> mentions) {
      this.mentions =
          ImmutableSet.copyOf(Iterables.transform(mentions, EquivalenceUtils.Wrap(MentionSpanEquivalence.equivalence())));
    }

    @Override
    public boolean apply(final ActorMention input) {
      checkNotNull(input);
      return mentions.contains(MentionSpanEquivalence.wrap(input.mention()));
    }
  }

  private static class ActorMentionMatchesSentence implements Predicate<ActorMention> {

    private final DocTheory docTheory;
    private final SentenceTheory sentenceTheory;

    private ActorMentionMatchesSentence(final DocTheory docTheory, final SentenceTheory sentenceTheory) {
      this.docTheory = docTheory;
      this.sentenceTheory = sentenceTheory;
    }

    @Override
    public boolean apply(final ActorMention input) {
      checkNotNull(input);
      // This will fall back on object equality, which is fine
      return input.mention().sentenceTheory(docTheory).equals(sentenceTheory);
    }
  }

  private enum ActorMentionToMentionFunction implements Function<ActorMention, Mention> {
    INSTANCE;

    @Override
    public Mention apply(final ActorMention input) {
      checkNotNull(input);
      return input.mention();
    }
  }
}
