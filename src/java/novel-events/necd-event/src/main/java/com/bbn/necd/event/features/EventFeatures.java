package com.bbn.necd.event.features;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.propositions.EventFilter;
import com.bbn.necd.event.propositions.PropositionEdge;
import com.bbn.necd.event.propositions.PropositionNode;
import com.bbn.necd.event.propositions.PropositionPredicateType;
import com.bbn.nlp.banks.wordnet.WordNetPOS;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.MoreObjects;
import com.google.common.base.Objects;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;

import java.util.Arrays;

import javax.annotation.Nullable;

import static com.bbn.necd.event.features.FeatureUtils.intArray;
import static com.bbn.necd.event.features.FeatureUtils.symbolArray;
import static com.bbn.necd.event.features.FeatureUtils.wordNetPOSArray;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Represents the features for an event.
 */
@JsonAutoDetect(fieldVisibility = Visibility.ANY, getterVisibility = Visibility.NONE, setterVisibility = Visibility.NONE)
public final class EventFeatures {
  private final Symbol id;
  @Nullable
  private final Symbol eventCode;
  private final PropositionPredicateType predType;
  private final EventFilter eventFilter;
  private final Symbol[] predicates;
  private final Symbol[] stems;
  private final WordNetPOS[] pos;
  private final Integer[] predicateTokenIndices;
  private final Symbol[] sourceSectors;
  private final Symbol[] targetSectors;
  private final Symbol[] sourceTokens;
  private final Symbol[] targetTokens;
  private final Symbol docId;
  private final int sentenceIndex;

  private final PropositionNode propTreeRoot;
  private final ImmutableList<PropositionEdge> propPathRootToSource;  // root -> source
  private final ImmutableList<PropositionEdge> propPathRootToTarget;  // root -> target
  private final ImmutableList<PropositionEdge> sourceNeighbors;
  private final ImmutableList<PropositionEdge> targetNeighbors;
  private final ImmutableList<ImmutableList<PropositionEdge>> sourceSharedPathsFromRoot;
  private final ImmutableList<ImmutableList<PropositionEdge>> targetSharedPathsFromRoot;

  private EventFeatures(
      @JsonProperty("id") Symbol id,
      @JsonProperty("eventCode") @Nullable Symbol eventCode,
      @JsonProperty("predType") PropositionPredicateType predType,
      @JsonProperty("eventFilter") EventFilter eventFilter,
      @JsonProperty("predicates") Symbol[] predicates,
      @JsonProperty("stems") Symbol[] stems,
      @JsonProperty("pos") WordNetPOS[] pos,
      @JsonProperty("predicateTokenIndices") Integer[] predicateTokenIndices,
      @JsonProperty("sourceSectors") Symbol[] sourceSectors,
      @JsonProperty("targetSectors") Symbol[] targetSectors,
      @JsonProperty("sourceTokens") Symbol[] sourceTokens,
      @JsonProperty("targetTokens") Symbol[] targetTokens,
      @JsonProperty("docId") Symbol docId,
      @JsonProperty("sentenceIndex") int sentenceIndex,
      @JsonProperty("propTreeRoot") PropositionNode propTreeRoot,
      @JsonProperty("propPathSourceToRoot") ImmutableList<PropositionEdge> propPathRootToSource,
      @JsonProperty("propPathRootToTarget") ImmutableList<PropositionEdge> propPathRootToTarget,
      @JsonProperty("sourceNeighbors") ImmutableList<PropositionEdge> sourceNeighbors,
      @JsonProperty("targetNeighbors") ImmutableList<PropositionEdge> targetNeighbors,
      @JsonProperty("sourceSharedPathsFromRoot") ImmutableList<ImmutableList<PropositionEdge>> sourceSharedPathsFromRoot,
      @JsonProperty("targetSharedPathsFromRoot") ImmutableList<ImmutableList<PropositionEdge>> targetSharedPathsFromRoot) {
    this.id = checkNotNull(id);
    this.predType = checkNotNull(predType);
    this.eventFilter = checkNotNull(eventFilter);
    this.predicates = checkNotNull(predicates);
    this.stems = checkNotNull(stems);
    this.pos = checkNotNull(pos);
    this.predicateTokenIndices = checkNotNull(predicateTokenIndices);
    this.sourceSectors = checkNotNull(sourceSectors);
    this.targetSectors = checkNotNull(targetSectors);
    this.sourceTokens = checkNotNull(sourceTokens);
    this.targetTokens = checkNotNull(targetTokens);
    this.docId = checkNotNull(docId);
    this.sentenceIndex = sentenceIndex;
    this.propTreeRoot = propTreeRoot;
    this.propPathRootToSource = propPathRootToSource;
    this.propPathRootToTarget = propPathRootToTarget;
    this.sourceNeighbors = sourceNeighbors;
    this.targetNeighbors = targetNeighbors;
    this.sourceSharedPathsFromRoot = sourceSharedPathsFromRoot;
    this.targetSharedPathsFromRoot = targetSharedPathsFromRoot;

    // Nullable
    this.eventCode = eventCode;
  }

  /*
  public static EventFeatures create(Symbol id, Optional<Symbol> eventCode, PropositionPredicateType predType,
      EventFilter eventFilter, Iterable<Symbol> predicates, Iterable<Symbol> stems, Iterable<WordNetPOS> pos,
      Iterable<Integer> predicateTokenIndices,
      Iterable<Symbol> sourceSectors, Iterable<Symbol> targetSectors, Iterable<Symbol> sourceTokens,
      Iterable<Symbol> targetTokens, Symbol docId, int sentenceIndex) {
    return new EventFeatures(id, eventCode.orNull(), predType, eventFilter, symbolArray(predicates),
        symbolArray(stems), wordNetPOSArray(pos), intArray(predicateTokenIndices), symbolArray(sourceSectors),
        symbolArray(targetSectors), symbolArray(sourceTokens), symbolArray(targetTokens),
        docId, sentenceIndex);
  }
  */

  public Symbol id() {
    return id;
  }

  public Optional<Symbol> eventCode() {
    return Optional.fromNullable(eventCode);
  }

  public PropositionPredicateType predType() {
    return predType;
  }

  public EventFilter eventFilter() {
    return eventFilter;
  }

  public ImmutableList<Symbol> predicates() {
    return ImmutableList.copyOf(predicates);
  }

  public ImmutableList<Symbol> stems() {
    return ImmutableList.copyOf(stems);
  }

  public ImmutableList<WordNetPOS> pos() {
    return ImmutableList.copyOf(pos);
  }

  public ImmutableList<Integer> predicateTokenIndices() {
    return ImmutableList.copyOf(predicateTokenIndices);
  }

  public ImmutableList<Symbol> sourceSectors() {
    return ImmutableList.copyOf(sourceSectors);
  }

  public ImmutableList<Symbol> targetSectors() {
    return ImmutableList.copyOf(targetSectors);
  }

  public ImmutableList<Symbol> sourceTokens() {
    return ImmutableList.copyOf(sourceTokens);
  }

  public ImmutableList<Symbol> targetTokens() {
    return ImmutableList.copyOf(targetTokens);
  }

  public Symbol docId() {
    return docId;
  }

  public int sentenceIndex() {
    return sentenceIndex;
  }

  public PropositionNode propTreeRoot() {
    return propTreeRoot;
  }

  public ImmutableList<PropositionEdge> propPathRootToSource() {
    return propPathRootToSource;
  }

  public ImmutableList<PropositionEdge> propPathRootToTarget() {
    return propPathRootToTarget;
  }

  public ImmutableList<PropositionEdge> sourceNeighbors() {
    return sourceNeighbors;
  }

  public ImmutableList<PropositionEdge> targetNeighbors() {
    return targetNeighbors;
  }

  public ImmutableList<ImmutableList<PropositionEdge>> sourceSharedPathsFromRoot() {
    return sourceSharedPathsFromRoot;
  }

  public ImmutableList<ImmutableList<PropositionEdge>> targetSharedPathsFromRoot() {
    return targetSharedPathsFromRoot;
  }

  public static Builder builder(final Symbol id, final Optional<Symbol> eventCode,
      final PropositionPredicateType predType, final EventFilter eventFilter, final Symbol docId,
      final int sentenceIndex) {
    return new Builder(id, eventCode, predType, eventFilter, docId, sentenceIndex);
  }

  public static final class Builder {
    private final Symbol id;

    private final Optional<Symbol> eventCode;
    private final PropositionPredicateType predType;
    private final EventFilter eventFilter;

    private final ImmutableList.Builder<Symbol> predicates;
    private final ImmutableList.Builder<Symbol> stems;
    private final ImmutableList.Builder<WordNetPOS> pos;
    private final ImmutableList.Builder<Integer> predicateTokenIndices;

    private final ImmutableSet.Builder<Symbol> sourceSectors;
    private final ImmutableSet.Builder<Symbol> targetSectors;
    private final ImmutableList.Builder<Symbol> sourceTokens;
    private final ImmutableList.Builder<Symbol> targetTokens;

    private final Symbol docId;
    private final int sentenceIndex;

    private PropositionNode propTreeRoot;
    private ImmutableList<PropositionEdge> propPathRootToSource;  // root -> source
    private ImmutableList<PropositionEdge> propPathRootToTarget;  // root -> target
    private ImmutableList<PropositionEdge> sourceNeighbors;
    private ImmutableList<PropositionEdge> targetNeighbors;
    private ImmutableList<ImmutableList<PropositionEdge>> sourceSharedPathsFromRoot;
    private ImmutableList<ImmutableList<PropositionEdge>> targetSharedPathsFromRoot;

    private Builder(final Symbol id, final Optional<Symbol> eventCode,
        final PropositionPredicateType predType, final EventFilter eventFilter, final Symbol docId,
        final int sentenceIndex) {
      this.id = id;
      this.eventCode = eventCode;
      this.predType = predType;
      this.eventFilter = eventFilter;
      this.docId = docId;
      this.sentenceIndex = sentenceIndex;

      this.predicates = ImmutableList.builder();
      this.stems = ImmutableList.builder();
      this.pos = ImmutableList.builder();
      this.predicateTokenIndices = ImmutableList.builder();
      this.sourceSectors = ImmutableSet.builder();
      this.targetSectors = ImmutableSet.builder();
      this.sourceTokens = ImmutableList.builder();
      this.targetTokens = ImmutableList.builder();

    }

    public Builder withPredicates(final ImmutableList<Symbol> predicates) {
      this.predicates.addAll(predicates);
      return this;
    }

    public Builder withStems(final ImmutableList<Symbol> stems) {
      this.stems.addAll(stems);
      return this;
    }

    public Builder withPos(final ImmutableList<WordNetPOS> pos) {
      this.pos.addAll(pos);
      return this;
    }

    public Builder withPredicateTokenIndices(final ImmutableList<Integer> predicateTokenIndices) {
      this.predicateTokenIndices.addAll(predicateTokenIndices);
      return this;
    }

    public Builder withSourceSectors(final ImmutableSet<Symbol> sourceSectors) {
      this.sourceSectors.addAll(sourceSectors);
      return this;
    }

    public Builder withTargetSectors(final ImmutableSet<Symbol> targetSectors) {
      this.targetSectors.addAll(targetSectors);
      return this;
    }

    public Builder withSourceTokens(final ImmutableList<Symbol> sourceTokens) {
      this.sourceTokens.addAll(sourceTokens);
      return this;
    }

    public Builder withTargetTokens(final ImmutableList<Symbol> targetTokens) {
      this.targetTokens.addAll(targetTokens);
      return this;
    }

    public Builder withPropTreeRoot(final PropositionNode node) {
      this.propTreeRoot = node;
      return this;
    }

    public Builder withPropPathRootToSource(final ImmutableList<PropositionEdge> path) {
      this.propPathRootToSource = path;
      return this;
    }

    public Builder withPropPathRootToTarget(final ImmutableList<PropositionEdge> path) {
      this.propPathRootToTarget = path;
      return this;
    }

    public Builder withSourceNeighbors(final ImmutableList<PropositionEdge> neighbors) {
      this.sourceNeighbors = neighbors;
      return this;
    }

    public Builder withTargetNeighbors(final ImmutableList<PropositionEdge> neighbors) {
      this.targetNeighbors = neighbors;
      return this;
    }

    public Builder withSourceSharedPathsFromRoot(final ImmutableList<ImmutableList<PropositionEdge>> paths) {
      this.sourceSharedPathsFromRoot = paths;
      return this;
    }

    public Builder withTargetSharedPathsFromRoot(final ImmutableList<ImmutableList<PropositionEdge>> paths) {
      this.targetSharedPathsFromRoot = paths;
      return this;
    }

    public EventFeatures build() {
      return new EventFeatures(id, eventCode.orNull(), predType, eventFilter,
          symbolArray(predicates.build()), symbolArray(stems.build()), wordNetPOSArray(pos.build()),
          intArray(predicateTokenIndices.build()),
          symbolArray(sourceSectors.build()), symbolArray(targetSectors.build()),
          symbolArray(sourceTokens.build()), symbolArray(targetTokens.build()),
          docId, sentenceIndex,
          propTreeRoot, propPathRootToSource, propPathRootToTarget,
          sourceNeighbors, targetNeighbors, sourceSharedPathsFromRoot, targetSharedPathsFromRoot);
    }
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(id, eventCode, predType, eventFilter, predicates, stems, pos, sourceSectors, targetSectors,
        sourceTokens, targetTokens, docId, sentenceIndex);
  }

  @Override
  public boolean equals(Object obj) {
    if (this == obj) {
      return true;
    }
    if (obj == null || getClass() != obj.getClass()) {
      return false;
    }
    final EventFeatures other = (EventFeatures) obj;
    return Objects.equal(this.id, other.id)
        && Objects.equal(this.eventCode, other.eventCode)
        && Objects.equal(this.predType, other.predType)
        && Objects.equal(this.eventFilter, other.eventFilter)
        && Arrays.equals(this.predicates, other.predicates)
        && Arrays.equals(this.stems, other.stems)
        && Arrays.equals(this.pos, other.pos)
        && Arrays.equals(this.sourceSectors, other.sourceSectors)
        && Arrays.equals(this.targetSectors, other.targetSectors)
        && Arrays.equals(this.sourceTokens, other.sourceTokens)
        && Arrays.equals(this.targetTokens, other.targetTokens)
        && Objects.equal(this.docId, other.docId)
        && Objects.equal(this.sentenceIndex, other.sentenceIndex);
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("id", id)
        .add("eventCode", eventCode)
        .add("predType", predType)
        .add("eventFilter", eventFilter)
        .add("predicates", predicates)
        .add("stems", stems)
        .add("pos", pos)
        .add("sourceSectors", sourceSectors)
        .add("targetSectors", targetSectors)
        .add("sourceTokens", sourceTokens)
        .add("targetTokens", targetTokens)
        .add("docId", docId)
        .add("sentenceIndex", sentenceIndex)
        .toString();
  }
}
