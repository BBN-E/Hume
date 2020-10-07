package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.nlp.WordAndPOS;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableListMultimap;
import com.google.common.collect.ImmutableMap;

// For each eventMention, add to its pattern-ID the canonical phrase of the eventMention's anchor

public final class EventMentionAnchorPhraseResolver implements DocumentResolver, Resolver {

  public final DocTheory resolve(final DocTheory docTheory) {
    final DocTheory.Builder docBuilder = docTheory.modifiedCopyBuilder();

    final ImmutableList.Builder<ImmutableList<WordAndPOS>> sentencesWordAndPosBuilder =
        ImmutableList.builder();
    for (int i = 0; i < docTheory.numSentences(); i++) {
      final ImmutableList.Builder<WordAndPOS> sentenceWordAndPosBuilder = ImmutableList.builder();
      final SentenceTheory st = docTheory.sentenceTheory(i);
      if (!st.parse().isAbsent() && st.parse().root().isPresent()) {
        final SynNode root = st.parse().root().get();
        for (int j = 0; j < root.numTerminals(); j++) {
          final SynNode node = root.nthTerminal(j);
          sentenceWordAndPosBuilder.add(WordAndPOS
              .fromWordThenPOS(Symbol.from(node.headWord().asString().toLowerCase()),
                  node.headPOS()));
        }
      }
      sentencesWordAndPosBuilder.add(sentenceWordAndPosBuilder.build());
    }
    final ImmutableList<ImmutableList<WordAndPOS>> sentencesWordAndPos =
        sentencesWordAndPosBuilder.build();
    // for each sentence, we now have the list of tokens (word, POS)

    final ImmutableListMultimap.Builder<String, EventMention> headword2eventMentionsBuilder =
        ImmutableListMultimap.builder();
    for (SentenceTheory sentenceTheory : docTheory.sentenceTheories()) {
      for (EventMention eventMention : sentenceTheory.eventMentions()) {
        String headword =
            eventMention.anchorNode().head().tokenSpan().tokenizedText(docTheory).utf16CodeUnits()
                .toLowerCase();
        headword2eventMentionsBuilder.put(headword, eventMention);
      }
    }
    final ImmutableListMultimap<String, EventMention> headword2eventMentions =
        headword2eventMentionsBuilder.build();
    // event mentions are now grouped by anchor headword

    // get headword noun phrase prefix
    final ImmutableMap.Builder<String, String> headword2phraseBuilder = ImmutableMap.builder();
    for (String headword : headword2eventMentions.keySet()) {
      String canonicalPhrase = headword;
      for (EventMention eventMention : headword2eventMentions.get(headword)) {
        final int anchorSentenceIndex =
            eventMention.anchorNode().sentenceTheory(docTheory).sentenceNumber();
        final int anchorHeadTokenIndex =
            eventMention.anchorNode().head().span().startToken().index();
        final ImmutableList<WordAndPOS> sentenceWordAndPos =
            sentencesWordAndPos.get(anchorSentenceIndex);

        if (sentenceWordAndPos.get(anchorHeadTokenIndex).POS().asString().equals("NN")) {
          int startIndex = anchorHeadTokenIndex;
          while (startIndex > 0 && (
              sentenceWordAndPos.get(startIndex - 1).POS().asString().equals("NN")
                  || sentenceWordAndPos.get(startIndex - 1).POS().asString().startsWith("JJ"))) {
            startIndex -= 1;
          }
          StringBuilder phraseBuilder = new StringBuilder();
          if ((anchorHeadTokenIndex - startIndex) > 2) {   // restrict to at most 3 tokens
            startIndex = anchorHeadTokenIndex - 2;
          }
          for (int i = startIndex; i <= anchorHeadTokenIndex; i++) {
            if (i > startIndex) {
              phraseBuilder.append(" ");
            }
            phraseBuilder.append(sentenceWordAndPos.get(i).word().asString());
          }
          String phrase = phraseBuilder.toString();
          if (phrase.length() > canonicalPhrase.length()) {
            canonicalPhrase = phrase;
          }
        }
      }
      headword2phraseBuilder.put(headword, canonicalPhrase);
    }
    final ImmutableMap<String, String> headword2phrase = headword2phraseBuilder.build();
    // for each trigger headword, we now have its canonical NP phrase

    for (int i = 0; i < docTheory.numSentences(); ++i) {
      final ImmutableList.Builder<EventMention> allEventMentionsBuilder = ImmutableList.builder();

      final SentenceTheory sentenceTheory = docTheory.sentenceTheory(i);
      for (EventMention eventMention : sentenceTheory.eventMentions()) {
        final int anchorSentenceIndex =
            eventMention.anchorNode().sentenceTheory(docTheory).sentenceNumber();
        final int anchorHeadTokenIndex =
            eventMention.anchorNode().head().span().startToken().index();
        final WordAndPOS wordAndPos =
            sentencesWordAndPos.get(anchorSentenceIndex).get(anchorHeadTokenIndex);

        String headword =
            eventMention.anchorNode().head().tokenSpan().tokenizedText(docTheory).utf16CodeUnits()
                .toLowerCase();

        if (eventMention.pattern().isPresent()) {
          final EventMention newEM =
              eventMention.modifiedCopyBuilder().setPatternID(eventMention.pattern().get()).build();
          allEventMentionsBuilder.add(newEM);
        } else {
          if (wordAndPos.POS().asString().equals("NN")) {
            final String anchorPhrase = headword2phrase.get(headword);
            final EventMention newEM =
                eventMention.modifiedCopyBuilder().setPatternID(Symbol.from(anchorPhrase)).build();
            allEventMentionsBuilder.add(newEM);
          } else {
            final EventMention newEM =
                eventMention.modifiedCopyBuilder().setPatternID(Symbol.from(headword)).build();
            allEventMentionsBuilder.add(newEM);
          }
        }
      }

      final SentenceTheory.Builder sentBuilder = sentenceTheory.modifiedCopyBuilder();
      sentBuilder.eventMentions(
          new EventMentions.Builder().eventMentions(allEventMentionsBuilder.build()).build());
      docBuilder.replacePrimarySentenceTheory(sentenceTheory, sentBuilder.build());
    }

    return docBuilder.build();
  }

}
