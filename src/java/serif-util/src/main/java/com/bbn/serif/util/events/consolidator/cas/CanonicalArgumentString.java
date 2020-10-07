package com.bbn.serif.util.events.consolidator.cas;

import com.bbn.serif.coreference.representativementions.FocusedRepresentativeMentionStrategy;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Entity;
import com.bbn.serif.theories.Entity.RepresentativeMention;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.util.events.consolidator.common.SieveUtils;

import com.google.common.base.Optional;

public class CanonicalArgumentString {
  final FocusedRepresentativeMentionStrategy casStrategy;

  public CanonicalArgumentString(final FocusedRepresentativeMentionStrategy casStrategy) {
    this.casStrategy = casStrategy;
  }

  public Optional<RepresentativeMention> getRepresentativeMention(final EventMention.Argument arg, final DocTheory doc) {
    final Optional<Mention> mention = SieveUtils.getEntityMention(arg);
    if(mention.isPresent()) {
      final Optional<Entity> entity = mention.get().entity(doc);
      if(entity.isPresent()) {
        return Optional.of(casStrategy.representativeMentionForEntity(entity.get(), mention.get()));
      }
    }
    return Optional.absent();
  }

  public Optional<String> getCASString(final EventMention.Argument arg, final DocTheory doc) {
    final Optional<RepresentativeMention> representativeMention = getRepresentativeMention(arg, doc);
    if(representativeMention.isPresent()) {
      return Optional.of(representativeMention.get().mention().span().tokenizedText().utf16CodeUnits());
    } else {
      return Optional.absent();
    }
  }

}
