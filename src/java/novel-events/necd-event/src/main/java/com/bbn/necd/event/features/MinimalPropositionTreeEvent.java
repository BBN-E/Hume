package com.bbn.necd.event.features;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.propositions.EventFilter;
import com.bbn.necd.event.propositions.PropositionPredicateType;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;

import java.util.List;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Provides a minimal implementation of {@link ProcessedEvent} for maximal memory savings.
 */
public final class MinimalPropositionTreeEvent implements ProcessedEvent {

  private final Symbol id;
  private final Symbol eventCode;
  private final ImmutableList<Symbol> predicates;
  private final ImmutableList<Symbol> stems;
  private final PropositionPredicateType predType;
  private final EventFilter eventFilter;

  private MinimalPropositionTreeEvent(Symbol id, @Nullable Symbol eventCode, List<Symbol> predicates,
      List<Symbol> stems, PropositionPredicateType predType, EventFilter eventFilter) {
    this.id = checkNotNull(id);
    this.predicates = ImmutableList.copyOf(predicates);
    this.stems = ImmutableList.copyOf(stems);
    this.predType = checkNotNull(predType);
    this.eventFilter = checkNotNull(eventFilter);
    // Nullable
    this.eventCode = eventCode;
  }

  @Nonnull
  public static MinimalPropositionTreeEvent fromEvent(PropositionTreeEvent eventFeatures) {
    return new MinimalPropositionTreeEvent(eventFeatures.getId(), eventFeatures.getEventCode().orNull(),
        eventFeatures.getPredicates(), eventFeatures.getStems(), eventFeatures.getPredType(),
        eventFeatures.getEventFilter());
  }

  @Override
  public Symbol getId() {
    return id;
  }

  @Override
  public Optional<Symbol> getEventCode() {
    return Optional.fromNullable(eventCode);
  }

  @Override
  public ImmutableList<Symbol> getPredicates() {
    return predicates;
  }

  @Override
  public ImmutableList<Symbol> getStems() {
    return stems;
  }

  @Override
  public PropositionPredicateType getPredType() {
    return predType;
  }

  @Override
  public EventFilter getEventFilter() {
    return eventFilter;
  }
}
