package com.bbn.necd.event.wrappers;

import com.bbn.necd.common.CollectionUtils;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Mention;
import com.google.common.annotations.Beta;
import com.google.common.base.Equivalence;
import com.google.common.base.MoreObjects;
import com.google.common.base.Objects;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Represent a pair of mentions.
 */
@Beta
public class MentionPair {
  private final Equivalence.Wrapper<Mention> mention1;
  private final Equivalence.Wrapper<Mention> mention2;

  private MentionPair(final Equivalence.Wrapper<Mention> mention1, final Equivalence.Wrapper<Mention> mention2) {
    this.mention1 = checkNotNull(mention1);
    this.mention2 = checkNotNull(mention2);
    // Check that they do not wrap null mentions
    checkNotNull(mention1.get());
    checkNotNull(mention2.get());
  }

  public static MentionPair fromPreservingOrder(final Equivalence.Wrapper<Mention> mention1, final Equivalence.Wrapper<Mention> mention2) {
    return new MentionPair(mention1, mention2);
  }

  public static MentionPair fromPreservingOrder(final Mention mention1, final Mention mention2) {
    return fromPreservingOrder(MentionSpanEquivalence.wrap(mention1), MentionSpanEquivalence.wrap(mention2));
  }

  public static MentionPair fromIgnoringOrder(final Equivalence.Wrapper<Mention> mention1, final Equivalence.Wrapper<Mention> mention2) {
    // Check that they are not null and do not wrap null mentions
    checkNotNull(mention1);
    checkNotNull(mention1.get());
    checkNotNull(mention2);
    checkNotNull(mention2.get());

    // Using mention1.getMention().span().startsBefore(mention2.getMention().span()) doesn't work
    if (CollectionUtils.spanPairIsInCorrectOrder(mention1.get().span(), mention2.get().span())) {
      return new MentionPair(mention1, mention2);
    } else {
      return new MentionPair(mention2, mention1);
    }
  }

  public static MentionPair fromIgnoringOrder(final Mention mention1, final Mention mention2) {
    return fromIgnoringOrder(MentionSpanEquivalence.wrap(mention1), MentionSpanEquivalence.wrap(mention2));
  }

  public Mention getFirstMention() {
    return mention1.get();
  }

  public Mention getSecondMention() {
    return mention2.get();
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(mention1, mention2);
  }

  @Override
  public boolean equals(final Object obj) {
    if (this == obj) {
      return true;
    }
    if (obj == null) {
      return false;
    }
    if (getClass() != obj.getClass()) {
      return false;
    }

    final MentionPair other = (MentionPair) obj;

    return Objects.equal(mention1, other.mention1) && Objects.equal(mention2, other.mention2);
  }


  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("mention1", mention1.get().head().terminalSymbols())
        .add("mention2", mention2.get().head().terminalSymbols())
        .toString();
  }

  public String asString(final DocTheory dt) {
    return MoreObjects.toStringHelper(this)
        .add("mention1", mention1.get().tokenSpan().tokenizedText(dt))
        .add("mention2", mention2.get().tokenSpan().tokenizedText(dt))
        .toString();
  }
}
