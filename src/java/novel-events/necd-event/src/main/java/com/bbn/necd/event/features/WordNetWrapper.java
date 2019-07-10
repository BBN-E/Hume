package com.bbn.necd.event.features;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.features.PropositionTreeEvent.WordPos;
import com.bbn.necd.wordnet.WordNetSimilarity;
import com.bbn.nlp.banks.wordnet.IWordNet;
import com.bbn.nlp.banks.wordnet.WordNetPOS;

import com.google.common.base.Function;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;

import java.util.List;

import javax.annotation.CheckForNull;
import javax.annotation.Nullable;

import static com.google.common.base.Preconditions.checkNotNull;
import static com.google.common.base.Preconditions.checkState;

/**
 * Wraps a WordNet instance.
 */
public final class WordNetWrapper {

  private final IWordNet wn;
  @CheckForNull
  private final WordNetSimilarity nounSim;
  @CheckForNull
  private final WordNetSimilarity verbSim;

  private WordNetWrapper(final IWordNet wn, @Nullable final WordNetSimilarity nounSim,
      @Nullable final WordNetSimilarity verbSim) {
    this.wn = checkNotNull(wn);
    this.nounSim = nounSim;
    this.verbSim = verbSim;
  }

  public static WordNetWrapper fromWordNet(final IWordNet wn, final WordNetSimilarity nounSim,
      final WordNetSimilarity verbSim) {
    return new WordNetWrapper(wn, nounSim, verbSim);
  }

  public ImmutableList<Symbol> getStems(List<WordPos> wordsWithPos) {
    final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();
    for (final WordPos wordPos : wordsWithPos) {
      final Symbol word = wordPos.word();
      final Optional<Symbol> optStem = getFirstStem(word, wordPos.pos());
      ret.add(optStem.isPresent() ? optStem.get() : word);
    }

    return ret.build();
  }

  public Optional<Symbol> getFirstStem(final Symbol word, final WordNetPOS pos) {
    return wn.getFirstStem(word, pos);
  }

  public ImmutableList<Symbol> getAllStems(final Symbol word, final WordNetPOS pos) {
    return wn.getAllStemsForWord(word, pos);
  }

  public Function<WordPosPair, Double> conSimFunction() {
    checkState(nounSim != null && verbSim != null,
        "Cannot produce ConSim measures unless similarity is supplied");
    return new ConSimFunction();
  }

  public Function<WordPosPair, Boolean> shareStemFunction() {
    return new ShareStemFunction();
  }

  public Function<WordPosPair, Boolean> shareSynsetFunction() {
    return new ShareSynsetFunction();
  }

  public Function<WordPosPair, Boolean> sameWordFunction() {
    return new SameWordFunction();
  }

  private class ConSimFunction implements Function<WordPosPair, Double> {
    @Override
    public Double apply(WordPosPair input) {
      checkNotNull(input);
      // Check nullable fields, just to be safe.
      checkNotNull(nounSim);
      checkNotNull(verbSim);
      final WordPos wordPos1 = input.wordPos1;
      final WordPos wordPos2 = input.wordPos2;
      // If the parts of speech don't match, for now return the minimum verb similarity
      if (!wordPos1.pos().equals(wordPos2.pos())) {
        return verbSim.wuPalmerMinConSim();
      }
      // Pick the pos and similarity source
      final WordNetPOS pos = wordPos1.pos();
      final WordNetSimilarity sim = pos.equals(WordNetPOS.NOUN) ? nounSim : verbSim;

      // Compute similarity
      final Optional<Symbol> optStem1 = getFirstStem(wordPos1.word(), pos);
      final Optional<Symbol> optStem2 = getFirstStem(wordPos2.word(), pos);
      if (optStem1.isPresent() && optStem2.isPresent()) {
        final Symbol stem1 = optStem1.get();
        final Symbol stem2 = optStem2.get();
        return sim.wuPalmerConSim(stem1, stem2).or(sim.wuPalmerMinConSim());
      } else {
        return sim.wuPalmerMinConSim();
      }
    }
  }

  private class ShareStemFunction implements Function<WordPosPair, Boolean> {
    @Override
    public Boolean apply(WordPosPair input) {
      checkNotNull(input);
      final WordPos wordPos1 = input.wordPos1;
      final WordPos wordPos2 = input.wordPos2;
      return !Sets.intersection(ImmutableSet.copyOf(getAllStems(wordPos1.word(), wordPos1.pos())),
          ImmutableSet.copyOf(getAllStems(wordPos2.word(), wordPos2.pos()))).isEmpty();
    }
  }

  private class ShareSynsetFunction implements Function<WordPosPair, Boolean> {
    @Override
    public Boolean apply(WordPosPair input) {
      checkNotNull(input);
      final WordPos wordPos1 = input.wordPos1;
      final WordPos wordPos2 = input.wordPos2;
      final ImmutableList<Symbol> stems1 = getAllStems(wordPos1.word(), wordPos1.pos());
      final ImmutableList<Symbol> stems2 = getAllStems(wordPos2.word(), wordPos2.pos());
      for (final Symbol stem1 : stems1) {
        for (final Symbol stem2 : stems2) {
          if (!Sets.intersection(ImmutableSet.copyOf(wn.getAllSynsetsOfStem(stem1, wordPos1.pos())),
              ImmutableSet.copyOf(wn.getAllSynsetsOfStem(stem2, wordPos2.pos()))).isEmpty()) {
            return true;
          }
        }
      }
      return false;
    }
  }

  private static class SameWordFunction implements Function<WordPosPair, Boolean> {
    @Override
    public Boolean apply(WordPosPair input) {
      checkNotNull(input);
      final WordPos wordPos1 = input.wordPos1;
      final WordPos wordPos2 = input.wordPos2;
      return wordPos1.word().equalTo(wordPos2.word());
    }
  }

  public static final class WordPosPair {
    private WordPos wordPos1;
    private WordPos wordPos2;

    private WordPosPair(WordPos wordPos1, WordPos wordPos2) {
      this.wordPos1 = checkNotNull(wordPos1);
      this.wordPos2 = checkNotNull(wordPos2);
    }

    static WordPosPair create(WordPos wordPos1, WordPos wordPos2) {
      return new WordPosPair(wordPos1, wordPos2);
    }
  }

}
