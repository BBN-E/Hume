package com.bbn.necd.event.propositions;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.Proposition;

/**
 * An enumeration of proposition roles.
 */
public enum PropositionRole {
  REF_ROLE,
  SUB_ROLE,
  OBJ_ROLE,
  IOBJ_ROLE,
  POSS_ROLE,
  TEMP_ROLE,
  LOC_ROLE,
  MEMBER_ROLE,
  UNKNOWN_ROLE,
  OTHER_ROLE,
  // A role made up just to support figuring out what is a terminal in a proposition tree
  TERMINAL_ROLE;

  // A special value used internally
  public static final Symbol TERMINAL_ROLE_SYMBOL = Symbol.from("TERMINAL_ROLE");

  /**
   * Returns the corresponding enum value for the symbol for a role.
   *
   * @param sym the symbol for the role
   * @return the corresponding enum value
   */
  public static PropositionRole fromSymbol(final Symbol sym) {
    if (sym.equalTo(Proposition.Argument.REF_ROLE)) {
      return REF_ROLE;
    } else if (sym.equalTo(Proposition.Argument.SUB_ROLE)) {
      return SUB_ROLE;
    } else if (sym.equalTo(Proposition.Argument.OBJ_ROLE)) {
      return OBJ_ROLE;
    } else if (sym.equalTo(Proposition.Argument.IOBJ_ROLE)) {
      return IOBJ_ROLE;
    } else if (sym.equalTo(Proposition.Argument.POSS_ROLE)) {
      return POSS_ROLE;
    } else if (sym.equalTo(Proposition.Argument.TEMP_ROLE)) {
      return TEMP_ROLE;
    } else if (sym.equalTo(Proposition.Argument.LOC_ROLE)) {
      return LOC_ROLE;
    } else if (sym.equalTo(Proposition.Argument.MEMBER_ROLE)) {
      return MEMBER_ROLE;
    } else if (sym.equalTo(Proposition.Argument.UNKNOWN_ROLE)) {
      return UNKNOWN_ROLE;
    } else if (sym.equalTo(TERMINAL_ROLE_SYMBOL)) {
      return TERMINAL_ROLE;
    } else {
      return OTHER_ROLE;
    }
  }
}
