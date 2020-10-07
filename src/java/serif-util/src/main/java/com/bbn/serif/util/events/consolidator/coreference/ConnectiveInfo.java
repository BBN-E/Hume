package com.bbn.serif.util.events.consolidator.coreference;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.util.events.consolidator.common.DocumentInfo;
import com.bbn.serif.util.events.consolidator.common.EventCandidate;
import com.bbn.serif.util.events.consolidator.common.NPChunks;
import com.bbn.serif.util.events.consolidator.common.WordInfo;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;

import java.util.List;

import static com.google.common.base.Preconditions.checkNotNull;

public class ConnectiveInfo {

  private final Connectives connectives;
  private final DocumentInfo documentInfo;

  public ConnectiveInfo(final Connectives connectives, final DocumentInfo documentInfo) {
    this.connectives = checkNotNull(connectives);
    this.documentInfo = checkNotNull(documentInfo);
  }

  public Indicators getIndicators(final DocTheory doc, final EventCandidate e1,
      final EventCandidate e2) {
    boolean hasComparisonContrastInBetween = false;
    boolean hasTemporalSynchronousInBetween = false;
    boolean hasCauseInBetween = false;
    boolean hasPreventionInBetween = false;
    boolean hasSingleDisjunctionInBetween = false;
    boolean hasCommaAndDisjunctionAroundSecondSpan = false;
    boolean hasSemiColonInBetween = false;
    boolean hasQuoteInBetween = false;
    boolean secondSpanHasPrefixAnother = false;

    for (final SynNode node1 : e1.getAnchorNodes()) {
      for (final SynNode node2 : e2.getAnchorNodes()) {
        final Indicators connectiveIndicators = getIndicators(doc, node1, node2);

        hasComparisonContrastInBetween =
            connectiveIndicators.hasComparisonContrastInBetween() || hasComparisonContrastInBetween;
        hasTemporalSynchronousInBetween =
            connectiveIndicators.hasTemporalSynchronousInBetween() || hasTemporalSynchronousInBetween;
        hasCauseInBetween = connectiveIndicators.hasCauseInBetween() || hasCauseInBetween;
        hasPreventionInBetween =
            connectiveIndicators.hasPreventionInBetween() || hasPreventionInBetween;
        hasSingleDisjunctionInBetween =
            connectiveIndicators.hasSingleDisjunctionInBetween() || hasSingleDisjunctionInBetween;
        hasCommaAndDisjunctionAroundSecondSpan =
            connectiveIndicators.hasCommaAndDisjunctionAroundSecondSpan() || hasCommaAndDisjunctionAroundSecondSpan;
        hasSemiColonInBetween =
            connectiveIndicators.hasSemiColonInBetween() || hasSemiColonInBetween;
        hasQuoteInBetween = connectiveIndicators.hasQuoteInBetween() || hasQuoteInBetween;
        secondSpanHasPrefixAnother =
            connectiveIndicators.secondSpanHasPrefixAnother() || secondSpanHasPrefixAnother;
      }
    }

    return new Indicators(hasComparisonContrastInBetween, hasTemporalSynchronousInBetween,
        hasCauseInBetween, hasPreventionInBetween, hasSingleDisjunctionInBetween,
        hasCommaAndDisjunctionAroundSecondSpan, hasSemiColonInBetween, hasQuoteInBetween,
        secondSpanHasPrefixAnother);
  }

  private Indicators getIndicators(final DocTheory doc, final SynNode node1, final SynNode node2) {

    final ImmutableList<WordInfo>
        wordsInfo = documentInfo.findConnectingWordInfo(doc, node1, node2);

    final boolean hasComparisonContrastInBetween = hasComparisonContrastInBetween(wordsInfo);
    final boolean hasTemporalSynchronousInBetween = hasTemporalSynchronousInBetween(wordsInfo);
    final boolean hasCauseInBetween = hasCauseInBetween(wordsInfo);
    final boolean hasPreventionInBetween = hasPreventionInBetween(wordsInfo);
    final boolean hasSingleDisjunctionInBetween = hasSingleDisjunctionInBetween(wordsInfo);
    final boolean hasCommaAndDisjunctionAroundSecondSpan =
        hasCommaAndDisjunctionAroundSecondSpan(doc, node1, node2, wordsInfo);
    final boolean hasSemiColonInBetween = hasSemiColonInBetween(wordsInfo);
    final boolean hasQuoteInBetween = hasQuoteInBetween(wordsInfo);
    final boolean secondSpanHasPrefixAnother = secondSpanHasPrefixAnother(doc, node1, node2);

    return new Indicators(hasComparisonContrastInBetween, hasTemporalSynchronousInBetween,
        hasCauseInBetween, hasPreventionInBetween,
        hasSingleDisjunctionInBetween, hasCommaAndDisjunctionAroundSecondSpan,
        hasSemiColonInBetween, hasQuoteInBetween,
        secondSpanHasPrefixAnother);
  }

  private boolean hasComparisonContrastInBetween(final ImmutableList<WordInfo> wordsInfo) {

    for (final WordInfo w : wordsInfo) {
      if (connectives.getComparisonContrastConnectives().contains(w.getLemma())) {
        return true;
      }
    }
    return false;
  }

  private boolean hasTemporalSynchronousInBetween(final ImmutableList<WordInfo> wordsInfo) {

    for (final WordInfo w : wordsInfo) {
      if (connectives.getTemporalSynchronousConnectives().contains(w.getLemma())) {
        return true;
      }
    }
    return false;
  }

  private boolean hasCauseInBetween(final ImmutableList<WordInfo> wordsInfo) {

    for (final WordInfo w : wordsInfo) {
      if (connectives.getCauseConnectives().contains(w.getLemma())) {
        return true;
      }
    }
    return false;
  }

  private boolean hasPreventionInBetween(final ImmutableList<WordInfo> wordsInfo) {

    for (final WordInfo w : wordsInfo) {
      if (connectives.getPreventionConnectives().contains(w.getLemma())) {
        return true;
      }
    }
    return false;
  }


  private boolean hasSingleDisjunctionInBetween(final ImmutableList<WordInfo> wordsInfo) {
    return (wordsInfo.size() == 1 && wordsInfo.get(0).getLemma() == OR);
  }

  private boolean hasCommaAndDisjunctionAroundSecondSpan(final DocTheory doc,
      final SynNode node1, final SynNode node2, final ImmutableList<WordInfo> wordsInfo) {

    final SynNode firstNode = getFirstNode(node1, node2);
    final SynNode secondNode = firstNode == node1 ? node2 : node1;

    if (wordsInfo.size() == 1 && wordsInfo.get(0).getLemma() == COMMA) {
      final ImmutableList<WordInfo> wordsInfoAfter =
          documentInfo.findWordInfoAfter(doc, secondNode);
      if (wordsInfoAfter.size() > 0 && wordsInfoAfter.get(0).getLemma() == OR) {
        return true;
      }
    }
    return false;
  }


  private boolean hasSemiColonInBetween(final ImmutableList<WordInfo> wordsInfo) {

    for (final WordInfo w : wordsInfo) {
      if (w.getLemma() == SEMICOLON) {
        return true;
      }
    }
    return false;
  }

  private boolean hasQuoteInBetween(final ImmutableList<WordInfo> wordsInfo) {

    for (final WordInfo w : wordsInfo) {
      if (w.getLemma() == OPEN_QUOTE || w.getLemma() == END_QUOTE) {
        return true;
      }
    }
    return false;
  }

  private boolean secondSpanHasPrefixAnother(final DocTheory doc,
      final SynNode node1, final SynNode node2) {

    final SynNode firstNode = getFirstNode(node1, node2);
    final SynNode secondNode = firstNode == node1 ? node2 : node1;

    final Symbol postag = secondNode.headPOS();

    if (postag.toString().startsWith("NN")) {  // anchor is a deverbal noun
      final int sentenceNumber = secondNode.sentenceTheory(doc).sentenceNumber();
      final Optional<NPChunks> np = documentInfo.getNPChunksForSentence(doc, sentenceNumber);

      if (np.isPresent()) {
        final Optional<ImmutableList<WordInfo>> wordsInfo =
            documentInfo.getWordsInfoForSentence(doc, sentenceNumber);
        final int npStart = nounPhraseStart(secondNode.span().startIndex(), np.get().npChunks());
        for (int i = npStart; i < secondNode.span().startIndex(); i++) {
          if (wordsInfo.get().get(i).getLemma() == ANOTHER) {
            return true;
          }
        }
      }

    }

    return false;
  }

  private SynNode getFirstNode(final SynNode node1, final SynNode node2) {
    return (node1.span().startIndex() <= node2.span().startIndex()) ? node1 : node2;
  }

  // copied from now deprecated AAUtils
  private int nounPhraseStart(final int start, final List<Symbol> npChunks) {
    int i = start;

    final Symbol begin = Symbol.from("B");
    final Symbol in = Symbol.from("I");

    while ((i > 0) && (npChunks.get(i - 1) == begin || npChunks.get(i - 1) == in)) {
      i -= 1;
    }
    return i;
  }

  private final Symbol OR = Symbol.from("or");
  private final Symbol COMMA = Symbol.from(",");
  private final Symbol SEMICOLON = Symbol.from(";");
  private final Symbol OPEN_QUOTE = Symbol.from("`");
  private final Symbol END_QUOTE = Symbol.from("'");
  private final Symbol ANOTHER = Symbol.from("another");




}

