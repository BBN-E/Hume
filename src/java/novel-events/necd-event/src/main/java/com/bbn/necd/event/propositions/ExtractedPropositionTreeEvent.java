package com.bbn.necd.event.propositions;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.actors.ActorMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;

import com.google.common.base.MoreObjects;
import com.google.common.base.Optional;

import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * A representation of an event instance using a proposition tree.
 */
public final class ExtractedPropositionTreeEvent {

  /**
   * The maximal proposition associated with the event.
   */
  private final PropositionTree tree;

  /**
   * The actors involved.
   */
  private final ActorMention source;
  private final ActorMention target;

  /**
   * The associated ICEWS event, which may be null.
   */
  private final ICEWSEventMention eventMention;

  /**
   * The document ID that the event instance came from.
   */
  private final Symbol docId;

  /*
   * Index of the sentence that the event instance came from
   */
  private final int sentenceIndex;

  /**
   * The number of hops on the path between source and target.
   */
  private final int hops;

  /**
   * The text of the sentence it came from.
   */
  private String sentenceText;

  private ExtractedPropositionTreeEvent(final PropositionTree tree, final ActorMention source,
      final ActorMention target, final ICEWSEventMention eventMention, final Symbol docId,
      final int sentenceIndex, final int hops, final String sentenceText) {
    this.tree = checkNotNull(tree);
    this.source = checkNotNull(source);
    this.target = checkNotNull(target);
    this.docId = checkNotNull(docId);
    this.sentenceIndex = sentenceIndex;
    checkArgument(hops > 0);
    this.hops = hops;
    this.sentenceText = checkNotNull(sentenceText);

    // May be null
    this.eventMention = eventMention;
  }

  public static ExtractedPropositionTreeEvent create(final PropositionTree tree, final ActorMention source,
      final ActorMention target, final Optional<ICEWSEventMention> eventMention, final Symbol docId,
      final int sentenceIndex, final int hops, final String sentenceText) {
    return new ExtractedPropositionTreeEvent(tree, source, target, eventMention.orNull(),
        docId, sentenceIndex, hops, sentenceText);
  }

  public PropositionTree getTree() {
    return tree;
  }

  public ActorMention getSource() {
    return source;
  }

  public ActorMention getTarget() {
    return target;
  }

  public Optional<ICEWSEventMention> getEventMention() {
    return Optional.fromNullable(eventMention);
  }

  public Symbol getDocId() {
    return docId;
  }

  public int getSentenceIndex() {
    return sentenceIndex;
  }

  public int getHops() {
    return hops;
  }

  public String getSentenceText() {
    return sentenceText;
  }

  public boolean hasEventMention() {
    return eventMention != null;
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("proposition", tree)
        .add("source", source)
        .add("target", target)
        .add("eventMention", eventMention)
        .add("docId", docId)
        .add("sentenceIndex", sentenceIndex)
        .toString();
  }
}
