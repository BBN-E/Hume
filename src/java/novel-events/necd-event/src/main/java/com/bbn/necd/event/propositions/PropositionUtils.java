package com.bbn.necd.event.propositions;

import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.Proposition.Argument;
import com.bbn.serif.theories.Proposition.MentionArgument;
import com.bbn.serif.theories.Proposition.PropositionArgument;

import com.google.common.annotations.Beta;
import com.google.common.base.Optional;
import com.google.common.base.Predicate;
import com.google.common.base.Predicates;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Maps;
import com.google.common.collect.Queues;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayDeque;
import java.util.List;
import java.util.Map;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Utilities for working with propositions.
 */
@Beta
public final class PropositionUtils {

  private static final Logger log = LoggerFactory.getLogger(PropositionUtils.class);

  private PropositionUtils() {
    throw new UnsupportedOperationException();
  }

  /**
   * Returns whether a proposition is verbal.
   *
   * @return true if it is a verbal proposition, false otherwise
   */
  public static Predicate<Proposition> isVerbalProposition() {
    return IsVerbalProposition.INSTANCE;
  }

  /**
   * Returns whether a proposition is nominal.
   *
   * @return true if it is a noun proposition, false otherwise
   */
  public static Predicate<Proposition> isNounProposition() {
    return IsNounProposition.INSTANCE;
  }

  /**
   * Returns whether a proposition is a name proposition.
   *
   * @return true if it is a name proposition, false otherwise
   */
  public static Predicate<Proposition> isNameProposition() {
    return IsNameProposition.INSTANCE;
  }

    /**
   * Returns whether a proposition is a pronoun proposition.
   *
   * @return true if it is a pronoun proposition, false otherwise
   */
  public static Predicate<Proposition> isPronounProposition() {
    return IsPronounProposition.INSTANCE;
  }

  /**
   * Returns whether an argument is reference argument. This requires that it have the {@code <ref>}
   * role and be an instance of a {@link MentionArgument}.
   *
   * @return true if it is a reference argument, false otherwise
   */
  public static Predicate<Argument> isReferenceArgument() {
    return IsReferenceArgument.INSTANCE;
  }

  /**
   * Returns the arguments of a set of {@link Proposition}s that are themselves {@link Proposition}s.
   *
   * @param props the propositions
   * @return a set of the propositional arguments of the specified propositions
   */
  public static ImmutableSet<Proposition> propositionalArguments(final ImmutableSet<Proposition> props) {
    final ImmutableSet.Builder<Proposition> ret = ImmutableSet.builder();
    for (final Proposition prop : props) {
      for (final Argument arg : Iterables.filter(prop.args(), Predicates.instanceOf(PropositionArgument.class))) {
        // The cast is always safe since we have already filtered by the type
        ret.add(((PropositionArgument) arg).proposition());
      }
    }
    return ret.build();
  }

  /**
   * Returns all mentions that are arguments of the specified proposition or its descendants,
   * omitting any mentions of role {@code <ref>}. Note that this can return duplicate mentions; use
   * {@link com.bbn.necd.event.wrappers.MentionSpanEquivalence} to de-deduplicate if needed.
   *
   * @param prop the root proposition
   * @return all mentions that are arguments of the proposition or its descendants
   */
  public static ImmutableList<Mention> mentionArguments(final Proposition prop) {
    final ImmutableList.Builder<Mention> ret = ImmutableList.builder();
    // Seed arguments with initial arguments
    final ArrayDeque<Argument> arguments = Queues.newArrayDeque(prop.args());
    while (!arguments.isEmpty()) {
      final Argument arg = arguments.pop();
      if (arg instanceof MentionArgument && !arg.roleIs(Argument.REF_ROLE)) {
        final MentionArgument mentionArg = (MentionArgument) arg;
        ret.add(mentionArg.mention());
      } else if (arg instanceof PropositionArgument) {
        final PropositionArgument propArg = (PropositionArgument) arg;
        arguments.addAll(propArg.proposition().args());
      }
      // We don't need to do anything for the TextArgument implementing class
    }
    return ret.build();
  }

  /**
   * Maps mention characters offsets to their definitional mentions. Unlike the CSERIF logic, of
   * PropositionSet::updateDefinitionsArray, this implementation restricts to nouns and
   * pronouns, processes in one pass, and ignore sets and modifiers.
   *
   * @param props  a set of propositions, some of which should be definitional
   * @return a map from the character offsets of mentions to the first defining proposition for that mention
   */
  public static ImmutableMap<OffsetRange<CharOffset>, Proposition> mapDefinitionalPropositions(
      final ImmutableSet<Proposition> props) {
    // We use a mutable map during construction since we need to check the contents while building
    final Map<OffsetRange<CharOffset>, Proposition> ret = Maps.newHashMap();

    // Add noun, pronoun
    for (final Proposition prop : Sets.filter(props,
        Predicates.or(IsNounProposition.INSTANCE, IsPronounProposition.INSTANCE))) {
      final Optional<MentionArgument> optArg = refArgument(prop.args());
      if (optArg.isPresent()) {
        final MentionArgument mentionArg = optArg.get();
        final OffsetRange<CharOffset> offsets = mentionArg.span().charOffsetRange();
        if (!ret.containsKey(offsets)) {
          ret.put(offsets, prop);
        }
      }
    }

    return ImmutableMap.copyOf(ret);
  }

  /**
   * Returns the {@code <ref>} role first argument, if it exists.
   *
   * @param args the arguments of a proposition
   * @return the reference argument or absent
   */
  public static Optional<MentionArgument> refArgument(final List<Argument> args) {
      if (!args.isEmpty() && IsReferenceArgument.INSTANCE.apply(args.get(0))) {
        return Optional.of((MentionArgument) args.get(0));
      } else {
        return Optional.absent();
      }
  }

  /**
   * Returns all arguments not of role {@code <ref>}. In theory, this could give inconsistent
   * results with {@link #refArgument(List)} if there is a {@code <ref>} argument after the first
   * argument. This situation is not believed to be possible.
   *
   * @param args the arguments of a proposition
   * @return all arguments with non-ref roles
   */
  public static ImmutableList<Argument> nonRefArguments(final List<Argument> args) {
    return FluentIterable.from(args).filter(Predicates.not(isReferenceArgument())).toList();
  }

  private enum IsVerbalProposition implements Predicate<Proposition> {
    INSTANCE;

    @Override
    public boolean apply(final Proposition input) {
      return input.predType().isVerbal();
    }
  }

  private enum IsNounProposition implements Predicate<Proposition> {
    INSTANCE;

    @Override
    public boolean apply(final Proposition input) {
      checkNotNull(input);
      final PropositionPredicateType predicateType = PropositionPredicateType.fromPredicateType(input.predType());
      return predicateType.equals(PropositionPredicateType.NOUN);
    }
  }

  private enum IsNameProposition implements Predicate<Proposition> {
    INSTANCE;

    @Override
    public boolean apply(final Proposition input) {
      checkNotNull(input);
      final PropositionPredicateType predicateType = PropositionPredicateType.fromPredicateType(input.predType());
      return predicateType.equals(PropositionPredicateType.NAME);
    }
  }

  private enum IsPronounProposition implements Predicate<Proposition> {
    INSTANCE;

    @Override
    public boolean apply(final Proposition input) {
      checkNotNull(input);
      final PropositionPredicateType predicateType = PropositionPredicateType.fromPredicateType(input.predType());
      return predicateType.equals(PropositionPredicateType.PRONOUN);
    }
  }

  private enum IsSetProposition implements Predicate<Proposition> {
    INSTANCE;

    @Override
    public boolean apply(final Proposition input) {
      checkNotNull(input);
      final PropositionPredicateType predicateType = PropositionPredicateType.fromPredicateType(input.predType());
      return predicateType.equals(PropositionPredicateType.SET);
    }
  }

  private enum IsReferenceArgument implements Predicate<Argument> {
    INSTANCE;

    @Override
    public boolean apply(final Argument input) {
      checkNotNull(input);
      return input.roleIs(Argument.REF_ROLE) && input instanceof MentionArgument;
    }
  }

  public static String prettyPrintProposition(final Proposition prop) {
    final StringBuilder sb = new StringBuilder();
    sb.append("[Prop Type=").append(prop.predType()).append(" ");
    if (prop.predHead().isPresent()) {
      sb.append("Head=").append(prop.predHead().get().terminalSymbols().toString()).append("; ");
    }
    sb.append("Args=[");
    boolean first = true;
    for (final Argument arg : prop.args()) {
      if (!first) {
        sb.append(", ");
      } else {
        first = false;
      }
      // Add the role if we have it
      if (arg.role().isPresent()) {
        sb.append("Role=").append(arg.role().get()).append(" ");
      }

      if (arg instanceof PropositionArgument) {
        sb.append(prettyPrintProposition(((PropositionArgument) arg).proposition()));
      } else if (arg instanceof MentionArgument) {
        final MentionArgument mentionArg = (MentionArgument) arg;
        sb.append("Mention: '")
            .append(mentionArg.span().tokenizedText())
            .append("'")
            .append(mentionArg.span().charOffsetRange());
      } else {
        sb.append("'").append(arg.span().tokenizedText()).append("'");
      }
    }
    sb.append("]]");
    return sb.toString();
  }

}
