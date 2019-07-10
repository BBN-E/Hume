package com.bbn.necd.event.wrappers;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.propositions.ExtractedPropositionTreeEvent;
import com.bbn.necd.event.propositions.PropositionPredicateType;
import com.bbn.necd.event.propositions.PropositionTree;
import com.bbn.necd.event.propositions.EventFilter;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.MoreObjects;
import com.google.common.base.Optional;

import javax.annotation.Nullable;

import static com.bbn.bue.common.StringUtils.SpaceJoiner;
import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Wrap the crucial fields of an {@link ExtractedPropositionTreeEvent} for serialization.
 */
public final class ExtractedPropositionTreeEventInfo {

  private final ActorMentionInfo source;
  private final ActorMentionInfo target;
  private final PropositionPredicateType predType;
  private final PropositionTree proposition;
  private final EventFilter eventFilter;
  @Nullable
  private final ICEWSEventMentionInfo icewsEventMentionInfo;
  private final Symbol docId;
  private final int sentenceIndex;
  private final int hops;
  private final String sentenceText;

  @JsonCreator
  private ExtractedPropositionTreeEventInfo(
      @JsonProperty("docId") final Symbol docId,
      @JsonProperty("sentenceIndex") final int sentenceIndex,
      @JsonProperty("source") final ActorMentionInfo source,
      @JsonProperty("target") final ActorMentionInfo target,
      @JsonProperty("predType") final PropositionPredicateType predType,
      @JsonProperty("proposition") final PropositionTree proposition,
      @JsonProperty("eventFilter") final EventFilter eventFilter,
      @JsonProperty("icewseventMentionInfo") @Nullable final ICEWSEventMentionInfo icewsEventMentionInfo,
      @JsonProperty("hops") final int hops,
      @JsonProperty("sentenceText") final String sentenceText) {
    this.docId = checkNotNull(docId);
    this.sentenceIndex = sentenceIndex;
    this.source = checkNotNull(source);
    this.predType = checkNotNull(predType);
    this.target = checkNotNull(target);
    this.proposition = checkNotNull(proposition);
    this.eventFilter = checkNotNull(eventFilter);
    checkArgument(hops > 0);
    this.hops = hops;
    this.sentenceText = checkNotNull(sentenceText);
    // May be null
    this.icewsEventMentionInfo = icewsEventMentionInfo;
  }

  public static ExtractedPropositionTreeEventInfo fromEvent(final ExtractedPropositionTreeEvent eventInstance,
      final EventFilter filter) {
    return new ExtractedPropositionTreeEventInfo(eventInstance.getDocId(),
        eventInstance.getSentenceIndex(),
        ActorMentionInfo.from(eventInstance.getSource()),
        ActorMentionInfo.from(eventInstance.getTarget()),
        eventInstance.getTree().root().predType(),
        eventInstance.getTree(),
        filter,
        ICEWSEventMentionInfo.fromICEWSEventMention(eventInstance.getEventMention()).orNull(),
        eventInstance.getHops(),
        eventInstance.getSentenceText());
  }

  public Symbol getDocId() {
    return docId;
  }

  public int getSentenceIndex() {
    return sentenceIndex;
  }

  public ActorMentionInfo getSource() {
    return source;
  }

  public ActorMentionInfo getTarget() {
    return target;
  }

  public PropositionPredicateType getPredType() {
    return predType;
  }

  public PropositionTree getProposition() {
    return proposition;
  }

  public Optional<ICEWSEventMentionInfo> getICEWSEventMentionInfo() {
    return Optional.fromNullable(icewsEventMentionInfo);
  }

  public String getSentenceText() {
    return sentenceText;
  }

  public EventFilter getEventFilter() {
    return eventFilter;
  }

  public int getHops() {
    return hops;
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("source", source)
        .add("target", target)
        .add("proposition", proposition)
        .add("icewsEventMentionInfo", icewsEventMentionInfo)
        .add("docId", docId)
        .add("sentenceIndex", sentenceIndex)
        .toString();
  }

  public String prettyPrint() {
    final StringBuilder sb = new StringBuilder();
    sb.append("Source: ").append(SpaceJoiner.join(source.getMention().getTokens())).append(" ").append(source.getActorId()).append("\n");
    sb.append("Target: ").append(SpaceJoiner.join(target.getMention().getTokens())).append(" ").append(target.getActorId()).append("\n");
    sb.append("Code: ").append(icewsEventMentionInfo != null ? icewsEventMentionInfo.getCode() : "(none)").append("\n");
    sb.append("Proposition:\n").append(proposition.prettyPrint());
    return sb.toString();
  }
}
