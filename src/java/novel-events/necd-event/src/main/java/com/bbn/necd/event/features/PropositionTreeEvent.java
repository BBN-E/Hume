package com.bbn.necd.event.features;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.icews.ActorType;
import com.bbn.necd.event.icews.CAMEOCodes;
import com.bbn.necd.event.propositions.EventFilter;
import com.bbn.necd.event.propositions.PropositionEdge;
import com.bbn.necd.event.propositions.PropositionNode;
import com.bbn.necd.event.propositions.PropositionPredicateType;
import com.bbn.necd.event.propositions.PropositionRole;
import com.bbn.necd.event.propositions.PropositionTree;
import com.bbn.necd.event.wrappers.ActorMentionInfo;
import com.bbn.necd.event.wrappers.ExtractedPropositionTreeEventInfo;
import com.bbn.necd.event.wrappers.ICEWSEventMentionInfo;
import com.bbn.necd.event.wrappers.MentionInfo;
import com.bbn.necd.event.wrappers.SynNodeInfo;
import com.bbn.nlp.banks.wordnet.WordNetPOS;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Queues;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayDeque;
import java.util.List;

import javax.annotation.Nullable;

import static com.bbn.necd.event.features.FeatureUtils.symbolArray;
import static com.bbn.necd.event.features.FeatureUtils.wordPosArray;
import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Represent features for events.
 */
@JsonAutoDetect(fieldVisibility = Visibility.ANY, getterVisibility = Visibility.NONE, setterVisibility = Visibility.NONE)
public final class PropositionTreeEvent implements ProcessedEvent {

  private static final Logger log = LoggerFactory.getLogger(PropositionTreeEvent.class);

  /**
   * A globally-unique identifier for the event.
   */
  private final Symbol id;

  /**
   * The document the event came from.
   */
  private final Symbol docId;

  /*
   * The index of the sentence the event came from
   */
  private final int sentenceIndex;

  /**
   * The code for the event. This is a CAMEO code, but may have been modified from the original coding. May be null.
   */
  @Nullable
  private final Symbol eventCode;

  /**
   * Predicates
   */
  private final WordPos[] predicatesWithPos;
  /**
   * Stemmed predicates
   */
  private final WordPos[] stemsWithPos;

  /**
   * The type of the root predicate
   */
  private final PropositionPredicateType predType;

  /**
   * Source actor information
   */
  private final long sourceActorId;
  private final ActorType sourceActorType;
  private final Symbol[] sourceTokens;

  /**
   * Target actor information
   */
  private final long targetActorId;
  private final ActorType targetActorType;
  private final Symbol[] targetTokens;

  /**
   * The number of hops in the path between source and target.
   */
  private final int hops;

  /**
   * The filter used to generate these features.
   */
  private final EventFilter eventFilter;

  /*
   * The proposition tree covering source and target mentions
   */
  private final PropositionTree propositionTree;

  /*
   * start and end char offsets of the source and target mentions
   */
  private final int sourceStartOffset;
  private final int sourceEndOffset;
  private final int targetStartOffset;
  private final int targetEndOffset;

  private PropositionTreeEvent(
      @JsonProperty("id") final Symbol id,
      @JsonProperty("docId") final Symbol docId,
      @JsonProperty("sentenceIndex") final int sentenceIndex,
      @JsonProperty("eventCode") @Nullable final Symbol eventCode,
      @JsonProperty("predType") final PropositionPredicateType predType,
      @JsonProperty("predicatesWithPos") final WordPos[] predicatesWithPos,
      @JsonProperty("stemsWithPos") final WordPos[] stemsWithPos,
      @JsonProperty("sourceActorId") final long sourceActorId,
      @JsonProperty("sourceActorType") final ActorType sourceActorType,
      @JsonProperty("sourceTokens") final Symbol[] sourceTokens,
      @JsonProperty("targetActorId") final long targetActorId,
      @JsonProperty("targetActorType") final ActorType targetActorType,
      @JsonProperty("targetTokens") final Symbol[] targetTokens,
      @JsonProperty("eventFilter") final EventFilter eventFilter,
      @JsonProperty("hops") final int hops,
      @JsonProperty("propositionTree") final PropositionTree propositionTree,
      @JsonProperty("sourceStartOffset") final int sourceStartOffset,
      @JsonProperty("sourceEndOffset") final int sourceEndOffset,
      @JsonProperty("targetStartOffset") final int targetStartOffset,
      @JsonProperty("targetEndOffset") final int targetEndOffset) {
    this.id = checkNotNull(id);
    this.docId = checkNotNull(docId);
    this.sentenceIndex = sentenceIndex;
    this.predType = checkNotNull(predType);
    this.sourceActorId = checkNotNull(sourceActorId);
    this.sourceActorType = checkNotNull(sourceActorType);
    this.targetActorId = checkNotNull(targetActorId);
    this.targetActorType = checkNotNull(targetActorType);
    this.eventFilter = checkNotNull(eventFilter);
    this.predicatesWithPos = checkNotNull(predicatesWithPos);
    this.stemsWithPos = checkNotNull(stemsWithPos);
    this.sourceTokens = checkNotNull(sourceTokens);
    this.targetTokens = checkNotNull(targetTokens);
    checkArgument(hops > 0);
    this.hops = hops;
    this.propositionTree = propositionTree;
    this.sourceStartOffset = sourceStartOffset;
    this.sourceEndOffset = sourceEndOffset;
    this.targetStartOffset = targetStartOffset;
    this.targetEndOffset = targetEndOffset;

    // May be null
    this.eventCode = eventCode;
  }

  public static Optional<PropositionTreeEvent> fromEventInstance(
      final ExtractedPropositionTreeEventInfo event, final WordNetWrapper wn) {
    final ActorMentionInfo source = event.getSource();
    final ActorMentionInfo target = event.getTarget();

    // Put together the ID from the document ID and offsets
    final Symbol id = formatId(event.getDocId(), source.getMention(), target.getMention());

    // Get the code if we can
    Optional<Symbol> code = Optional.absent();
    final Optional<ICEWSEventMentionInfo> optICEWSEvent = event.getICEWSEventMentionInfo();
    if (optICEWSEvent.isPresent()) {
      final ICEWSEventMentionInfo icewsEvent = optICEWSEvent.get();
      // Convert the code
      final Optional<Symbol> newCode = CAMEOCodes.transformCode(icewsEvent.getCode());
      // If this is absent, that means the code is one we should be ignoring. Skip this event entirely.
      if (!newCode.isPresent()) {
        return Optional.absent();
      } else {
        code = newCode;
      }
    }

    // Get predicates
    final ImmutableList<WordPos> predicates = extractPredicates(event);
    final ImmutableList<WordPos> stems = stemPredicates(predicates, wn);
    // Skip if the predicates should be rejected
    if (rejectPredicates(predicates)) {
      return Optional.absent();
    }

    return Optional.of(new PropositionTreeEvent(id, event.getDocId(), event.getSentenceIndex(), code.orNull(), event.getPredType(),
        wordPosArray(predicates), wordPosArray(stems), source.getActorId(), source.getActorType(),
        symbolArray(source.getMention().getTokens()), target.getActorId(), target.getActorType(),
        symbolArray(target.getMention().getTokens()), event.getEventFilter(), event.getHops(), event.getProposition(),
        source.getMention().getStartOffset(), source.getMention().getEndOffset(),
        target.getMention().getStartOffset(), target.getMention().getEndOffset()));
  }

  @Override
  public Symbol getId() {
    return id;
  }

  public Symbol getDocId() {
    return docId;
  }

  public int getSentenceIndex() {
    return sentenceIndex;
  }

  @Override
  public Optional<Symbol> getEventCode() {
    return Optional.fromNullable(eventCode);
  }

  @Override
  public PropositionPredicateType getPredType() {
    return predType;
  }

  @Override
  public ImmutableList<Symbol> getPredicates() {
    final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();
    for (final WordPos wordPos : predicatesWithPos) {
      ret.add(wordPos.word());
    }
    return ret.build();
  }

  @Override
  public ImmutableList<Symbol> getStems() {
    final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();
    for (final WordPos wordPos : stemsWithPos) {
      ret.add(wordPos.word());
    }
    return ret.build();
  }

  public ImmutableList<Integer> getPredicateTokenIndices() {
    final ImmutableList.Builder<Integer> ret = ImmutableList.builder();
    for(final WordPos wordPos : predicatesWithPos) {
      ret.add(wordPos.tokenIndex());
    }
    return ret.build();
  }

  public ImmutableList<WordNetPOS> getPos() {
    final ImmutableList.Builder<WordNetPOS> ret = ImmutableList.builder();
    for (final WordPos wordPos : predicatesWithPos) {
      ret.add(wordPos.pos());
    }
    return ret.build();
  }

  public ImmutableList<WordPos> getPredicatesWithPos() {
    return ImmutableList.copyOf(predicatesWithPos);
  }

  public ImmutableList<WordPos> getStemsWithPos() {
    return ImmutableList.copyOf(stemsWithPos);
  }

  public long getSourceActorId() {
    return sourceActorId;
  }

  public long getTargetActorId() {
    return targetActorId;
  }

  public ActorType getSourceActorType() {
    return sourceActorType;
  }

  public ActorType getTargetActorType() {
    return targetActorType;
  }

  public ImmutableList<Symbol> getSourceTokens() {
    return ImmutableList.copyOf(sourceTokens);
  }

  public ImmutableList<Symbol> getTargetTokens() {
    return ImmutableList.copyOf(targetTokens);
  }

  @Override
  public EventFilter getEventFilter() {
    return eventFilter;
  }

  public int getHops() {
    return hops;
  }

  public PropositionTree getPropositionTree() {
    return propositionTree;
  }

  public int getSourceStartOffset() {
    return sourceStartOffset;
  }

  public int getSourceEndOffset() {
    return sourceEndOffset;
  }

  public int getTargetStartOffset() {
    return targetStartOffset;
  }

  public int getTargetEndOffset() {
    return targetEndOffset;
  }

  /**
   * Returns whether predicates should be rejected.
   *
   * @param predicates the predicates to evaluate, which may be empty but cannot be null
   * @return whether to reject the predicates
   */
  private static boolean rejectPredicates(final List<WordPos> predicates) {
    if (predicates.isEmpty()) {
      return true;
    }
    // Guaranteed to succeed since we checked for empty already
    final Symbol firstPredicate = predicates.get(0).word();

    // Check if the first predicate is good
    if (CAMEOCodes.isIgnoredPredicate(firstPredicate)) {
      return true;
    }

    // Reject any empty predicates and predicates with '_' in them. It's unclear what creates these, but they can cause
    // problems down the line when given to WordNet.
    for (final WordPos wordPos : predicates) {
      final String predicateString = wordPos.word().asString();
      if (predicateString.isEmpty() || predicateString.contains("_")) {
        return true;
      }
    }

    return false;
  }

  private static ImmutableList<WordPos> extractPredicates(final ExtractedPropositionTreeEventInfo event) {
    final PropositionNode rootProposition = event.getProposition().root();
    final ActorMentionInfo source = event.getSource();
    final ActorMentionInfo target = event.getTarget();
    final ImmutableList.Builder<WordPos> preds = ImmutableList.builder();

    // Traverse the proposition graph, adding predicates as we find them
    final ArrayDeque<PropositionWithRole> propositions = Queues.newArrayDeque();
    propositions.add(PropositionWithRole.create(rootProposition, PropositionRole.UNKNOWN_ROLE));
    int nounsAdded = 0;
    boolean addedAnything = false;
    while (!propositions.isEmpty()) {
      final PropositionWithRole propRole = propositions.pop();
      final PropositionNode prop = propRole.proposition;
      final PropositionRole role = propRole.role;
      switch (prop.predType()) {
        case VERB:
          // Add the verb itself if this is the root or an object
          if ((prop.equals(rootProposition) || role.equals(PropositionRole.OBJ_ROLE) || role.equals(PropositionRole.IOBJ_ROLE))
              && prop.head().isPresent()) {
            final Symbol word = prop.head().get().getHeadWord();
            preds.add(WordPos.create(word, WordNetPOS.VERB, prop.head().get().getHeadTokenIndex()));
            addedAnything = true;
          }
          break;
        case NOUN:
          final WordNetPOS pos = WordNetPOS.NOUN;
          // We need a head to do anything
          if (prop.head().isPresent()) {
            final SynNodeInfo head = prop.head().get();
            if (prop.equals(rootProposition)) {
              // Always add if it's the root proposition
              preds.add(WordPos.create(head.getHeadWord(), pos, head.getHeadTokenIndex()));
              nounsAdded++;
              addedAnything = true;
            } else if (nounsAdded == 0
                && (role.equals(PropositionRole.OBJ_ROLE) || role.equals(PropositionRole.IOBJ_ROLE))
                && !source.getMention().contains(head.getStartOffset(), head.getEndOffset())
                && !target.getMention().contains(head.getStartOffset(), head.getEndOffset())) {
              // Add if we haven't added any nouns yet, the head is in an object role, and is not the source/target
              preds.add(WordPos.create(head.getHeadWord(), pos, head.getHeadTokenIndex()));
              nounsAdded++;
              addedAnything = true;
            }
          }
          break;
        default:
          // Do nothing
      }
      // Recurse on the arguments if we saw anything here. This check exists so we don't start recursing down into
      // overly specific arguments if we didn't see anything at the higher level.
      if (addedAnything) {
        for (final PropositionEdge arg : prop.children()) {
          propositions.add(PropositionWithRole.create(arg.node(), arg.label()));
        }
      }
    }

    return preds.build();
  }

  private static ImmutableList<WordPos> stemPredicates(final ImmutableList<WordPos> predicates,
      final WordNetWrapper wn) {
    final ImmutableList.Builder<WordPos> ret = ImmutableList.builder();
    for (final WordPos wordPos : predicates) {
      final Symbol word = wordPos.word();
      final WordNetPOS pos = wordPos.pos();
      ret.add(WordPos.create(wn.getFirstStem(word, pos).or(word), pos, wordPos.tokenIndex()));
    }
    return ret.build();
  }

  private static Symbol formatId(final Symbol docId, final MentionInfo sourceMention, final MentionInfo targetMention) {
    return Symbol.from(docId.asString() + "[" + sourceMention.getStartOffset() + "-" + sourceMention.getEndOffset()
        + ":" + targetMention.getStartOffset() + "-" + targetMention.getEndOffset() + "]");
  }

  private static class PropositionWithRole {
    private PropositionNode proposition;
    private PropositionRole role;

    private PropositionWithRole(PropositionNode proposition, PropositionRole role) {
      this.proposition = proposition;
      this.role = role;
    }

    private static PropositionWithRole create(PropositionNode proposition, PropositionRole role) {
      return new PropositionWithRole(proposition, role);
    }
  }

  final static class WordPos {
    private final Symbol word;
    private final WordNetPOS pos;
    private final int tokenIndex; // overloading this class, to include (sentence) token index of this word

    private WordPos(
        @JsonProperty("word") Symbol word,
        @JsonProperty("pos") WordNetPOS pos,
        @JsonProperty("tokenIndex") int tokenIndex) {
      this.word = checkNotNull(word);
      this.pos = checkNotNull(pos);
      this.tokenIndex = tokenIndex;
    }

    static WordPos create(Symbol word, WordNetPOS pos, int tokenIndex) {
      return new WordPos(word, pos, tokenIndex);
    }

    @JsonProperty("word")
    public Symbol word() {
      return word;
    }

    @JsonProperty("pos")
    public WordNetPOS pos() {
      return pos;
    }

    @JsonProperty("tokenIndex")
    public int tokenIndex() {
      return tokenIndex;
    }

    public String toString() {
      return word.asString() + "/" + pos;
    }
  }
}
