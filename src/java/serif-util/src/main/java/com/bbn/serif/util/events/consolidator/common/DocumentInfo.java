package com.bbn.serif.util.events.consolidator.common;

import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.bue.geonames.GeonamesException;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.theories.TokenSequence;
import com.bbn.serif.util.events.consolidator.coreference.SieveKnowledge;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;

import java.io.IOException;

public class DocumentInfo {
  private final SentenceWordsInfo sentenceWordsInfo;
  private final SentenceNPs sentenceNPs;
  private final PlaceContainmentCache placeContainmentCache;
  private final PropPathCache propPathCache;

  public DocumentInfo(final SieveKnowledge sieveKnowledge, final DocTheory doc)
      throws GeonamesException, IOException {
    this.sentenceWordsInfo = SentenceWordsInfo.from(doc, sieveKnowledge.language(), sieveKnowledge.stemmer());
    this.sentenceNPs = SentenceNPs.from(doc);
    this.placeContainmentCache = new PlaceContainmentCache(sieveKnowledge.geonames(), sieveKnowledge.cas(), doc);
    this.propPathCache = new PropPathCache(sieveKnowledge.language(), sieveKnowledge.stemmer(), doc);
  }

  public SentenceWordsInfo sentenceWordsInfo() {
    return this.sentenceWordsInfo;
  }

  public SentenceNPs sentenceNPs() {
    return this.sentenceNPs;
  }

  public PlaceContainmentCache placeContainmentCache() {
    return this.placeContainmentCache;
  }

  public PropPathCache propPathCache() {
    return this.propPathCache;
  }

  public ImmutableList<WordInfo> findWordInfoBefore(final DocTheory doc, final SynNode node) {
    final ImmutableList.Builder<WordInfo> ret = ImmutableList.builder();
    final int sentenceNumber = node.sentenceTheory(doc).sentenceNumber();
    if (sentenceWordsInfo.toMap().containsKey(sentenceNumber)) {
      final ImmutableList<WordInfo> words = sentenceWordsInfo.toMap().get(sentenceNumber);
      for (int i = 0; i < node.span().startIndex(); i++) {
        ret.add(words.get(i));
      }
    }
    return ret.build();
  }

  public ImmutableList<WordInfo> findWordInfoAfter(final DocTheory doc, final SynNode node) {
    final ImmutableList.Builder<WordInfo> ret = ImmutableList.builder();
    final int sentenceNumber = node.sentenceTheory(doc).sentenceNumber();
    if (sentenceWordsInfo.toMap().containsKey(sentenceNumber)) {
      final ImmutableList<WordInfo> words = sentenceWordsInfo.toMap().get(sentenceNumber);
      for (int i = (node.span().endIndex() + 1); i < words.size(); i++) {
        ret.add(words.get(i));
      }
    }
    return ret.build();
  }

  public ImmutableList<WordInfo> findConnectingWordInfo(final DocTheory doc,
      final SynNode node1, final SynNode node2) {

    final ImmutableList.Builder<WordInfo> ret = ImmutableList.builder();
    final int n1 = node1.sentenceTheory(doc).sentenceNumber();
    final int n2 = node2.sentenceTheory(doc).sentenceNumber();

    if (n1 == n2) {
      final Optional<OffsetRange<CharOffset>> offset = findConnectingOffset(node1.span(), node2.span());
      // if absent, it means node1 and node2 overlap in spans
      if (offset.isPresent()) {
        final int start = offset.get().startInclusive().asInt();
        final int end = offset.get().endInclusive().asInt();

        if (this.sentenceWordsInfo.toMap().containsKey(n1)) {
          final ImmutableList<WordInfo> words = this.sentenceWordsInfo.toMap().get(n1);
          for (int i = start; i <= end; i++) {
            ret.add(words.get(i));
          }
        }
      }
    } // else, this is an error; we will assume this would not happen for the time being
    return ret.build();
  }

  private Optional<OffsetRange<CharOffset>> findConnectingOffset(final TokenSequence.Span span1,
      final TokenSequence.Span span2) {
    final int span1Start = span1.startIndex();
    final int span1End = span1.endIndex();
    final int span2Start = span2.startIndex();
    final int span2End = span2.endIndex();

    if ((span1End + 1) < span2Start) {
      return Optional.of(OffsetRange.charOffsetRange(span1End + 1, span2Start - 1));
    } else if ((span2End + 1) < span1Start) {
      return Optional.of(OffsetRange.charOffsetRange(span2End + 1, span1Start - 1));
    } else {
      return Optional.absent();
    }
  }

  public Optional<ImmutableList<WordInfo>> getWordsInfoForSentence(final DocTheory doc,
      final int sentenceNumber) {
    return Optional.fromNullable(sentenceWordsInfo.toMap().get(sentenceNumber));
  }

  public Optional<NPChunks> getNPChunksForSentence(final DocTheory doc,
      final int sentenceNumber) {
    return Optional.fromNullable(sentenceNPs.toMap().get(sentenceNumber));
  }

}
