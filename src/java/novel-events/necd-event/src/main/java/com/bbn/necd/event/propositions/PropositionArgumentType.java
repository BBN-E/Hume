package com.bbn.necd.event.propositions;

import com.bbn.serif.theories.Proposition;

/**
 * Defines proposition argument types.
 */
public enum PropositionArgumentType {
  MENTION,
  PROPOSITION,
  TEXT;

  /**
   * Returns the corresponding enum value for a {@link Proposition.Argument}.
   *
   * @param arg the argument
   * @return the corresponding enum value
   */
  public static PropositionArgumentType fromArgument(final Proposition.Argument arg) {
    if (arg instanceof Proposition.MentionArgument) {
      return MENTION;
    } else if (arg instanceof Proposition.PropositionArgument) {
      return PROPOSITION;
    } else if (arg instanceof Proposition.TextArgument) {
      return TEXT;
    } else {
      throw new UnsupportedOperationException("Unhandled argument type");
    }
  }
}
