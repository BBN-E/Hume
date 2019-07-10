package com.bbn.necd.event.features;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.icews.ActorType;
import com.bbn.necd.event.icews.CAMEOCodes;
import com.bbn.necd.event.icews.ICEWSEventInstance;
import com.bbn.necd.event.wrappers.ICEWSEventMentionInfo;
import com.google.common.base.Function;
import com.google.common.base.Objects;
import com.google.common.base.Optional;

import static com.google.common.base.Preconditions.checkArgument;

/**
 * Represent features for events.
 */
public final class ICEWSEventFeatures {
  private final Symbol id;        // a globally unique identifier

  private final Symbol eventCode;
  private final Symbol tense;
  private final Symbol predicate;
  private final long actorId1;
  private final long actorId2;
  private final ActorType actorType1;
  private final ActorType actorType2;

  private ICEWSEventFeatures(final Symbol id, final Symbol eventCode, final Symbol tense, final Symbol predicate,
      final long actorId1, final ActorType actorType1, final long actorId2, final ActorType actorType2) {
    this.id = id;
    this.eventCode = eventCode;
    this.tense = tense;
    this.predicate = predicate;
    this.actorId1 = actorId1;
    this.actorType1 = actorType1;
    this.actorId2 = actorId2;
    this.actorType2 = actorType2;
  }

  public Symbol getId() {
    return id;
  }

  public Symbol getEventCode() {
    return eventCode;
  }

  public Symbol getTense() {
    return tense;
  }

  public Symbol getPredicate() {
    return predicate;
  }

  public long getActorId1() {
    return actorId1;
  }

  public long getActorId2() {
    return actorId2;
  }

  public ActorType getActorType1() {
    return actorType1;
  }

  public ActorType getActorType2() {
    return actorType2;
  }

  public static ICEWSEventFeatures fromEventInstance(final ICEWSEventInstance event) {
    checkArgument(event.getICEWSEventMentionInfo().isPresent());

    final ICEWSEventMentionInfo info = event.getICEWSEventMentionInfo().get();
    // Return null if this is a code we don't want
    final Symbol code = info.getCode();
    // Convert the code
    final Optional<Symbol> newCode = CAMEOCodes.transformCode(code);
    if (!newCode.isPresent()) {
      return null;
    }

    final ICEWSEventInstance.Argument arg1 = event.getArguments().get(0);
    final ICEWSEventInstance.Argument arg2 = event.getArguments().get(1);

    return new ICEWSEventFeatures(
        Symbol.from("1"),
        newCode.get(),
        info.getTense(),
        event.getPredicate(),
        arg1.getActorId(),
        arg1.getActorType(),
        arg2.getActorId(),
        arg2.getActorType()
    );
  }

  @Override
  public boolean equals(final Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }

    final ICEWSEventFeatures that = (ICEWSEventFeatures) o;
    return Objects.equal(this.eventCode, that.eventCode) &&
        Objects.equal(this.tense, that.tense) &&
        Objects.equal(this.predicate, that.predicate) &&
        Objects.equal(this.actorId1, that.actorId1) &&
        Objects.equal(this.actorId2, that.actorId2);
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(eventCode, tense, predicate, actorId1, actorId2);
  }


  public enum ExtractFeaturesFunction implements Function<ICEWSEventInstance, ICEWSEventFeatures> {
    INSTANCE;

    @Override
    public ICEWSEventFeatures apply(final ICEWSEventInstance input) {
      return fromEventInstance(input);
    }
  }

  public enum EventCodeFunction implements Function<ICEWSEventFeatures, Symbol> {
    INSTANCE;

    @Override
    public Symbol apply(final ICEWSEventFeatures input) {
      return input.eventCode;
    }
  }
}
