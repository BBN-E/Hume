package com.bbn.serif.util.events.consolidator.coreference;

public final class Indicators {

  private final boolean hasComparisonContrastInBetween;
  private final boolean hasTemporalSynchronousInBetween;
  private final boolean hasCauseInBetween;
  private final boolean hasPreventionInBetween;
  private final boolean hasSingleDisjunctionInBetween;
  private final boolean hasCommaAndDisjunctionAroundSecondSpan;
  private final boolean hasSemiColonInBetween;
  private final boolean hasQuoteInBetween;
  private final boolean secondSpanHasPrefixAnother;

  Indicators(final boolean hasComparisonContrastInBetween,
      final boolean hasTemporalSynchronousInBetween,
      final boolean hasCauseInBetween,
      final boolean hasPreventionInBetween,
      final boolean hasSingleDisjunctionInBetween,
      final boolean hasCommaAndDisjunctionAroundSecondSpan,
      final boolean hasSemiColonInBetween,
      final boolean hasQuoteInBetween,
      final boolean secondSpanHasPrefixAnother) {
    this.hasComparisonContrastInBetween = hasComparisonContrastInBetween;
    this.hasTemporalSynchronousInBetween = hasTemporalSynchronousInBetween;
    this.hasCauseInBetween = hasCauseInBetween;
    this.hasPreventionInBetween = hasPreventionInBetween;
    this.hasSingleDisjunctionInBetween = hasSingleDisjunctionInBetween;
    this.hasCommaAndDisjunctionAroundSecondSpan = hasCommaAndDisjunctionAroundSecondSpan;
    this.hasSemiColonInBetween = hasSemiColonInBetween;
    this.hasQuoteInBetween = hasQuoteInBetween;
    this.secondSpanHasPrefixAnother = secondSpanHasPrefixAnother;
  }


  public boolean hasComparisonContrastInBetween() {
    return hasComparisonContrastInBetween;
  }

  public boolean hasTemporalSynchronousInBetween() {
    return hasTemporalSynchronousInBetween;
  }

  public boolean hasCauseInBetween() {
    return hasCauseInBetween;
  }

  public boolean hasPreventionInBetween() {
    return hasPreventionInBetween;
  }

  public boolean hasSingleDisjunctionInBetween() {
    return hasSingleDisjunctionInBetween;
  }

  public boolean hasCommaAndDisjunctionAroundSecondSpan() {
    return hasCommaAndDisjunctionAroundSecondSpan;
  }

  public boolean hasSemiColonInBetween() {
    return hasSemiColonInBetween;
  }

  public boolean hasQuoteInBetween() {
    return hasQuoteInBetween;
  }

  public boolean secondSpanHasPrefixAnother() {
    return secondSpanHasPrefixAnother;
  }
}
