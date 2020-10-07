package com.bbn.serif.util.events.consolidator.common;

import com.bbn.bue.common.symbols.Symbol;

public final class WordInfo {
  private final Symbol word;
  private final Symbol postag;
  private final Symbol lemma;

  private WordInfo(final Symbol word, final Symbol postag, final Symbol lemma) {
    this.word = word;
    this.postag = postag;
    this.lemma = lemma;
  }

  public static WordInfo from(final Symbol word, final Symbol postag, final Symbol lemma) {
    return new WordInfo(word, postag, lemma);
  }

  public Symbol getWord() {
    return word;
  }

  public Symbol getPostag() {
    return postag;
  }

  public Symbol getLemma() {
    return lemma;
  }
}
