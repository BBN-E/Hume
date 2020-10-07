package com.bbn.serif.util.events.consolidator.common;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.nlp.languages.LanguageSpecific;
import com.bbn.serif.theories.Parse;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.TokenSequence;

import java.util.ArrayList;
import java.util.List;

/**
 * This is copied here from serif-events-graveyard
 */
@LanguageSpecific("English")
public class NPChunks {

  private final List<Symbol> npChunks;

  private NPChunks(List<Symbol> npChunks) {
    this.npChunks = npChunks;
  }

  public List<Symbol> npChunks() {
    return npChunks;
  }

  @LanguageSpecific("English")
  public static NPChunks create(SentenceTheory sentenceTheory) {
    List<Symbol> chunks = new ArrayList<>();
    final TokenSequence tokens = sentenceTheory.tokenSequence();
    final Parse parse = sentenceTheory.parse();

    final Symbol beginTag = Symbol.from("B");
    final Symbol inTag = Symbol.from("I");
    final Symbol outTag = Symbol.from("O");
    // first, identify the nouns, pronouns, and dates
    for (int i = 0; i < tokens.size(); i++) {
      final String postag = parse.root().get().nthTerminal(i).parent().get().tag().toString();
      if (postag.startsWith("NN") || postag.startsWith("PRP")
          || postag.compareTo("DATE-NNP") == 0) {
        chunks.add(inTag);
      } else {
        chunks.add(outTag);
      }
    }

    // now, do a second pass and identify the NP boundaries
    for (int i = 0; i < chunks.size(); i++) {
      if (chunks.get(i) == inTag) {
        String currentTag =
            parse.root().get().nthTerminal(i).parent().get().tag().toString();
        int j = i;
        while (j > 0) {
          final String ltag =
              parse.root().get().nthTerminal(j - 1).parent().get().tag().toString();
          if (ltag.startsWith("JJ") ||  // adjective
              ltag.compareTo("CD") == 0 ||  // cardinal number
              (ltag.compareTo("NN") == 0 && currentTag.compareTo("NN") == 0) ||  // first half of noun-noun compound
              ltag.compareTo("DT") == 0 || ltag.compareTo("PDT") == 0) {  // determiner or predeterminer
            chunks.set(j - 1, inTag);
            j -= 1;
          } else {
            break;
          }
          currentTag = ltag;
        }
        chunks.set(j, beginTag);
      }
    }

    return new NPChunks(chunks);
  }
}
