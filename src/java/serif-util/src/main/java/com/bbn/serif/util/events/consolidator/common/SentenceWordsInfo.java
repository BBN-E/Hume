package com.bbn.serif.util.events.consolidator.common;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.nlp.languages.Language;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Parse;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.TokenSequence;
import com.bbn.serif.util.events.consolidator.proputil.Stemmer;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;

public final class SentenceWordsInfo {
  private final ImmutableMap<Integer, ImmutableList<WordInfo>> sentenceWordsInfo;

  private SentenceWordsInfo(final ImmutableMap<Integer, ImmutableList<WordInfo>> sentenceWordsInfo) {
    this.sentenceWordsInfo = sentenceWordsInfo;
  }

  public static SentenceWordsInfo from(final DocTheory doc, final Language language, final Stemmer stemmer) {
    final ImmutableMap.Builder<Integer, ImmutableList<WordInfo>>
        sentenceWordsInfoBuilder = ImmutableMap.builder();

    for (final SentenceTheory st : doc.nonEmptySentenceTheories()) {
      final int sentenceNumber = st.sentenceNumber();

      final ImmutableList<Symbol> words = sentenceWordTokens(st);
      final ImmutableList<Symbol> posTags = sentencePosTags(st);
      final ImmutableList<Symbol> lemmas = sentenceLemmaTokens(words, posTags, language, stemmer);

      final ImmutableList.Builder<WordInfo> wordsInfo = ImmutableList.builder();
      for (int i = 0; i < words.size(); i++) {
        final WordInfo wordInfo = WordInfo.from(words.get(i), posTags.get(i), lemmas.get(i));
        wordsInfo.add(wordInfo);
      }
      sentenceWordsInfoBuilder.put(sentenceNumber, wordsInfo.build());
    }

    return new SentenceWordsInfo(sentenceWordsInfoBuilder.build());
  }

  // pos tags of a sentence
  private static ImmutableList<Symbol> sentencePosTags(final SentenceTheory st) {
    final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();

    final TokenSequence tokenSequence = st.tokenSequence();
    final Parse parse = st.parse();

    for (int i = 0; i < tokenSequence.size(); i++) {
      final Symbol postag = parse.root().get().nthTerminal(i).parent().get().tag();
      ret.add(postag);
    }

    return ret.build();
  }

  // words of a sentence
  private static ImmutableList<Symbol> sentenceWordTokens(final SentenceTheory st) {
    final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();

    final TokenSequence tokenSequence = st.tokenSequence();
    for (int i = 0; i < tokenSequence.size(); i++) {
      final Symbol word = tokenSequence.token(i).symbol();
      ret.add(word);
    }

    return ret.build();
  }

  // lemmas of a sentence
  private static ImmutableList<Symbol> sentenceLemmaTokens(final ImmutableList<Symbol> words,
      final ImmutableList<Symbol> posTags, final Language language, final Stemmer stemmer) {
    final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();

    for (int i = 0; i < words.size(); i++) {
      final Symbol lc = Symbol.from(language.lowercase(words.get(i).toString()));
      final Symbol stem = stemmer.stem(lc, posTags.get(i));
      ret.add(stem);
    }

    return ret.build();
  }

  public ImmutableMap<Integer, ImmutableList<WordInfo>> toMap() {
    return sentenceWordsInfo;
  }
}

