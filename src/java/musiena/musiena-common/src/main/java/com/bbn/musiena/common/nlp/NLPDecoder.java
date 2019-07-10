package com.bbn.musiena.common.nlp;


import com.google.common.base.Joiner;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Sets;

import java.io.IOException;
import java.util.Set;

public final class NLPDecoder {
  private final SentenceSegmenter sentenceSegmenter;
  private final TokenDecoder tokenDecoder;
  private final Lemmatizer lemmatizer;

  public NLPDecoder() throws IOException {
    this.sentenceSegmenter = SentenceSegmenter.from(SENTENCE_MODEL);
    this.tokenDecoder = TokenDecoder.from(TOKEN_MODEL);
    this.lemmatizer = Lemmatizer.from(LEMMA_DICTIONARY);
  }

  public ImmutableList<String> sentenceSegment(final String input) {
    return sentenceSegmenter.decode(input);
  }

  public String toTokenizedString(final String input) {
    return tokenDecoder.decodeAsString(input);
  }

  public ImmutableList<String> toSegmentedTokenizedStrings(final String input) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    for(final String s : sentenceSegmenter.decode(input)) {
      ret.add(tokenDecoder.decodeAsString(s));
    }

    return ret.build();
  }

  public ImmutableList<String> toSegmentedTokenizedNormalizedStrings(final String input) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    for(final String s : sentenceSegmenter.decode(input)) {
      ret.add(normalize(tokenDecoder.decode(s)));
    }

    return ret.build();
  }


  public String normalize(final ImmutableList<String> tokens) {
    final ImmutableList.Builder<String> sb = ImmutableList.builder();

    for(final String token : tokens) {
      if(!brackets.contains(token) && !quotes.contains(token) && !punctuations.contains(token)) {
        sb.add(lemmatizer.getLemma(token));
      }
    }

    final String s = Joiner.on(" ").join(sb.build());
    return s.toLowerCase().replace(" e .g. ", " ").replace("  ", " ");
  }

  private static final String SENTENCE_MODEL = "en-sent.bin";
  private static final String TOKEN_MODEL = "en-token.bin";
  public static final String LEMMA_DICTIONARY = "lemma.nv";

  private static final Set<String> brackets = Sets.newHashSet("[", "]", "(", ")", "{", "}", "<", ">");
  private static final Set<String> quotes = Sets.newHashSet("'", "``", "''", "\"");
  private static final Set<String> punctuations = Sets.newHashSet(".", ",", ":", ";", "?", "!", "&", "@", "*", "+", "#");
}
