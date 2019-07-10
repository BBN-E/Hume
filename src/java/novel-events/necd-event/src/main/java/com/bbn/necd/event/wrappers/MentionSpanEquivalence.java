package com.bbn.necd.event.wrappers;

import com.bbn.serif.theories.Mention;
import com.google.common.annotations.Beta;
import com.google.common.base.Equivalence;
import com.google.common.base.Objects;

/**
 * An {@link Equivalence} that compares and hashes {@link Mention}s by span. Since equivalences are abstract classes,
 * this cannot use the usual enum approach to implement the singleton pattern.
 */
@Beta
public class MentionSpanEquivalence {

  /**
   * An equivalence that compares and hashes mentions by span.
   */
  private static final Equivalence<Mention> INSTANCE = new Equivalence<Mention>() {
    @Override
    protected boolean doEquivalent(final Mention a, final Mention b) {
      return Objects.equal(a.span(), b.span());
    }

    @Override
    protected int doHash(final Mention mention) {
      return Objects.hashCode(mention.span());
    }
  };

  private MentionSpanEquivalence() {
    throw new UnsupportedOperationException();
  }

  /**
   * A singleton equivalence that compares and hashes mentions by span.
   *
   * @return the equivalence
   */
  public static Equivalence<Mention> equivalence() {
    return INSTANCE;
  }

  /**
   * Wrap a mention using equivalence that compares and hashes mentions by span.
   *
   * @param mention the mention
   * @return the wrapped mention
   */
  public static Equivalence.Wrapper<Mention> wrap(final Mention mention) {
    return INSTANCE.wrap(mention);
  }
}
