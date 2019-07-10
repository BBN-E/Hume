package com.bbn.necd.event.propositions;

import com.bbn.serif.theories.Proposition;

/**
 * An enumeration of proposition predicate types.
 */
public enum PropositionPredicateType {
  VERB,
  COPULA,
  MODIFIER,
  NOUN,
  POSS,
  LOC,
  SET,
  NAME,
  PRONOUN,
  COMP;

  /**
   * Returns the corresponding enum value for the specified predicate type.
   *
   * @param predicateType the predicate type
   * @return the corresponding enum value
   */
  public static PropositionPredicateType fromPredicateType(final Proposition.PredicateType predicateType) {
    if (predicateType.name().equalTo(Proposition.PredicateType.VERB.name())) {
      return VERB;
    } else if (predicateType.name().equalTo(Proposition.PredicateType.COPULA.name())) {
      return COPULA;
    } else if (predicateType.name().equalTo(Proposition.PredicateType.MODIFIER.name())) {
      return MODIFIER;
    } else if (predicateType.name().equalTo(Proposition.PredicateType.NOUN.name())) {
      return NOUN;
    } else if (predicateType.name().equalTo(Proposition.PredicateType.POSS.name())) {
      return POSS;
    } else if (predicateType.name().equalTo(Proposition.PredicateType.LOC.name())) {
      return LOC;
    } else if (predicateType.name().equalTo(Proposition.PredicateType.SET.name())) {
      return SET;
    } else if (predicateType.name().equalTo(Proposition.PredicateType.NAME.name())) {
      return NAME;
    } else if (predicateType.name().equalTo(Proposition.PredicateType.PRONOUN.name())) {
      return PRONOUN;
    } else if (predicateType.name().equalTo(Proposition.PredicateType.COMP.name())) {
      return COMP;
    } else {
      throw new UnsupportedOperationException("Unhandled predicate type");
    }
  }
}
