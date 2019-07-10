package com.bbn.necd.event.wrappers;

import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.types.EntityType;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.Function;
import com.google.common.base.MoreObjects;
import com.google.common.base.Objects;
import com.google.common.collect.ImmutableList;

import java.io.Serializable;

import static com.bbn.necd.event.TheoryUtils.mentionTokens;

/**
 * Wrap the crucial fields of a {@link com.bbn.serif.theories.Mention} for serialization.
 */
public final class MentionInfo implements Serializable {

  private final ImmutableList<Symbol> tokens;
  private final int startOffset;
  private final int endOffset;
  private final EntityType entityType;
  // we probably should make EntitySubtype itself serializable, but for simplicity, we'll use Symbol for now
  private final Symbol entitySubtype;

  private MentionInfo(
      @JsonProperty("tokens") final ImmutableList<Symbol> tokens,
      @JsonProperty("startOffset") final int startOffset,
      @JsonProperty("endOffset") final int endOffset,
      @JsonProperty("entityType") final EntityType entityType,
      @JsonProperty("entitySubtype") final Symbol entitySubtype) {
    this.tokens = tokens;
    this.startOffset = startOffset;
    this.endOffset = endOffset;
    this.entityType = entityType;
    this.entitySubtype = entitySubtype;
  }

  public static MentionInfo from(final Mention mention) {
    // Extract tokens
    final ImmutableList<Symbol> tokens = mentionTokens(mention);
    final OffsetRange<CharOffset> offsetRange = mention.span().charOffsetRange();

    return new MentionInfo(tokens, offsetRange.startInclusive().asInt(),
        offsetRange.endInclusive().asInt(), mention.entityType(), mention.entitySubtype().name());
  }

  public static Function<Mention, MentionInfo>  mentionInfoFromMentionFunction() {
    return MentionInfoFromMentionFunction.INSTANCE;
  }

  public ImmutableList<Symbol> getTokens() {
    return tokens;
  }

  public int getStartOffset() {
    return startOffset;
  }

  public int getEndOffset() {
    return endOffset;
  }

  public EntityType getEntityType() {
    return entityType;
  }

  public Symbol getEntitySubtype() {
    return entitySubtype;
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("tokens", tokens)
        .add("startOffset", startOffset)
        .add("endOffset", endOffset)
        .toString();
  }

  @Override
  public boolean equals(final Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    final MentionInfo that = (MentionInfo) o;
    return startOffset == that.startOffset &&
        endOffset == that.endOffset &&
        Objects.equal(tokens, that.tokens) &&
        Objects.equal(entityType, that.entityType) &&
        Objects.equal(entitySubtype, that.entitySubtype);
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(tokens, startOffset, endOffset, entityType, entitySubtype);
  }

  /**
   * Returns true if the specified mention matches the offsets of this object.
   */
  public boolean equalTo(final Mention mention) {
    final OffsetRange<CharOffset> offsets = mention.span().charOffsetRange();
    return startOffset == offsets.startInclusive().asInt() && endOffset == offsets.endInclusive().asInt();
  }

  public boolean equalTo(final OffsetRange<CharOffset> offsets) {
    return startOffset == offsets.startInclusive().asInt() && endOffset == offsets.endInclusive().asInt();
  }

  public boolean contains(final int startOffset, final int endOffset) {
    return this.startOffset <= startOffset && this.endOffset >= endOffset;
  }

  public boolean contains(final MentionInfo mentionInfo) {
    return contains(mentionInfo.startOffset, mentionInfo.endOffset);
  }

  private enum MentionInfoFromMentionFunction implements Function<Mention, MentionInfo> {
    INSTANCE;

    @Override
    public MentionInfo apply(final Mention mention) {
      return from(mention);
    }
  }

}
