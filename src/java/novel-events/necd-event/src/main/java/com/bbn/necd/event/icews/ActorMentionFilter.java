package com.bbn.necd.event.icews;

import com.bbn.bue.common.StringUtils;
import com.bbn.bue.common.symbols.SymbolUtils;
import com.bbn.necd.event.TheoryUtils;
import com.bbn.serif.theories.actors.ActorMention;
import com.bbn.serif.types.EntityType;

import com.google.common.base.Predicate;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;

/**
 * Predicates that filter down actor mentions to allowable mentions.
 */
public enum ActorMentionFilter implements Predicate<ActorMention> {
  ANY {
    @Override
    public boolean apply(final ActorMention input) {
      return true;
    }
  },

  EVENT_DISCOVERY {
    public boolean apply(final ActorMention input) {
      final ImmutableList<String> tokens =
          FluentIterable.from(TheoryUtils.mentionTokens(input.mention()))
              .transform(SymbolUtils.desymbolizeFunction())
              .transform(StringUtils.ToLowerCase)
              .toList();

      // If the tokens are empty for some reason, filter it out
      if (tokens.isEmpty()) {
        return false;
      }

      // Returning true means we should keep it, so we check that it is an allowed entity type
      // and does not contain any of the bad tokens
      return allowedEntityType(input.mention().entityType()) &&
          !(FILTERED_FIRST_WORDS.contains(tokens.get(0))
                || FILTERED_MULTI_WORDS.contains(tokens)
                || Iterables.any(tokens, MatchesFilteredWords.INSTANCE));
    }

    private boolean allowedEntityType(final EntityType entityType) {
      return entityType.matchesPER() || entityType.matchesORG() || entityType.matchesGPE();
    }
  };

  private static final ImmutableSet<String> FILTERED_WORDS = ImmutableSet.of(
      "here",
      "there",
      "this",
      "that",
      "these",
      "those",
      "everyone",
      "everybody",
      "everywhere",
      "everything",
      "someone",
      "somebody",
      "somewhere",
      "something",
      "anyone",
      "anybody",
      "anywhere",
      "anything",
      "noone",
      "no-one",
      "nobody",
      "nowhere",
      "nothing",
      "myself",
      "yourself",
      "himself",
      "herself",
      "itself",
      "ourselves",
      "yourselves",
      "themselves",
      "i",
      "me",
      "my",
      "mine",
      "we",
      "us",
      "our",
      "ours",
      "you",
      "your",
      "yours",
      "whoever",
      "whomever"
  );

  private static final ImmutableSet<String> FILTERED_FIRST_WORDS = ImmutableSet.of(
      "any"
  );

  private static final ImmutableList<ImmutableList<String>> FILTERED_MULTI_WORDS = ImmutableList.of(
      ImmutableList.of("no", "one")
  );

  private enum MatchesFilteredWords implements Predicate<String> {
    INSTANCE;

    @Override
    public boolean apply(final String input) {
      return FILTERED_WORDS.contains(input);
    }
  }
}
