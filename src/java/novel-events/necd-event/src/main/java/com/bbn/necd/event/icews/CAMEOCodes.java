package com.bbn.necd.event.icews;

import com.bbn.bue.common.symbols.Symbol;
import com.google.common.annotations.Beta;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

/**
 * Utilities for working with CAMEO codes.
 */
@Beta
public final class CAMEOCodes {

  private static final ImmutableSet<String> IGNORE_CODES = ImmutableSet.of(
      "010", "043", "0861"
  );

  private static final ImmutableMap<String, String> COLLAPSED_CODES = ImmutableMap.of(
      // No codes currently being collapsed
  );

  private static final ImmutableSet<String> IGNORE_PREDICATES = ImmutableSet.of(
      "say",
      "says",
      "said",
      "tell",
      "tells",
      "told",
      "speak",
      "speaks",
      "spoke"
  );

  /**
   * Truncate a CAMEO code to a useful number of digits, currently three.
   * @param code the code
   * @return the truncated version of the code
   */
  public static Symbol truncateCode(final Symbol code) {
    return Symbol.from(code.asString().substring(0, 3));
  }

  /**
   * Truncate a CAMEO code to a top-level code, defined as the first two digits.
   * @param code the code
   * @return the top-level version of the code
   */
  public static Symbol topLevelCode(final Symbol code) {
    return Symbol.from(code.asString().substring(0, 2));
  }

  /**
   * Transform a CAMEO code by truncating it and applying any exclusions or code merging required.
   * @param code the original code
   * @return the transformed code
   */
  public static Optional<Symbol> transformCode(final Symbol code) {
    // Truncate code
    final Symbol truncatedCode = truncateCode(code);

    if (IGNORE_CODES.contains(truncatedCode.asString()) || IGNORE_CODES.contains(code.asString())) {
      return Optional.absent();
    }

    final String newCode = COLLAPSED_CODES.get(truncatedCode.asString());
    return Optional.of(newCode == null ? truncatedCode : Symbol.from(newCode));
  }

  /**
   * Returns whether a predicate is in the set of ignored top-level predicates.
   */
  public static boolean isIgnoredPredicate(final Symbol predicate) {
    return IGNORE_PREDICATES.contains(predicate.asString());
  }
}
