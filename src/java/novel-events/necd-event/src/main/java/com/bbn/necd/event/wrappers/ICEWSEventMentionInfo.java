package com.bbn.necd.event.wrappers;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.MoreObjects;
import com.google.common.base.Optional;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Wrap the crucial fields from an ICEWS event.
 */
public final class ICEWSEventMentionInfo {
  private final Symbol code;
  private final Symbol tense;
  private final Symbol patternId;

  private ICEWSEventMentionInfo(
      @JsonProperty("code") final Symbol code,
      @JsonProperty("tense") final Symbol tense,
      @JsonProperty("patternId") final Symbol patternId) {
    this.code = checkNotNull(code);
    this.tense = checkNotNull(tense);
    this.patternId = checkNotNull(patternId);
  }

  public static ICEWSEventMentionInfo from(final Symbol code, final Symbol tense, final Symbol patternId) {
    return new ICEWSEventMentionInfo(code, tense, patternId);
  }

  public static ICEWSEventMentionInfo fromICEWSEventMention(final ICEWSEventMention eventMention) {
    return new ICEWSEventMentionInfo(eventMention.code(), eventMention.tense(),
        eventMention.patternId());
  }

  public static Optional<ICEWSEventMentionInfo> fromICEWSEventMention(final Optional<ICEWSEventMention> eventMention) {
    return eventMention.isPresent()
        ? Optional.of(fromICEWSEventMention(eventMention.get()))
        : Optional.<ICEWSEventMentionInfo>absent();
  }

  public Symbol getCode() {
    return code;
  }

  public Symbol getTense() {
    return tense;
  }

  public Symbol getPatternId() {
    return patternId;
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("code", code)
        .add("tense", tense)
        .add("patternId", patternId)
        .toString();
  }
}
