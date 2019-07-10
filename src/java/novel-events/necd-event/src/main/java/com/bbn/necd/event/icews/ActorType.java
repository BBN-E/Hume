package com.bbn.necd.event.icews;

import com.bbn.serif.theories.actors.ActorMention;
import com.bbn.serif.theories.actors.CompositeActorMention;
import com.bbn.serif.theories.actors.ProperNounActorMention;
import com.bbn.serif.theories.actors.SimpleActorMention;

import static com.google.common.base.Preconditions.checkState;

/**
 * Extract information for different types of ActorMention implementations.
 */
public enum ActorType {
  PROPER_NOUN,
  COMPOSITE,
  SIMPLE;

  public static long getActorId(final ActorMention actorMention) {
    final ActorType actorType = ActorType.getType(actorMention);
    return actorType.actorId(actorMention);
  }

  public static ActorType getType(final ActorMention actorMention) {
    if (actorMention instanceof ProperNounActorMention) {
      return PROPER_NOUN;
    } else if (actorMention instanceof CompositeActorMention) {
      return COMPOSITE;
    } else if (actorMention instanceof SimpleActorMention) {
      return SIMPLE;
    } else {
      throw new IllegalArgumentException("Unhandled ActorMention implementing class: " + actorMention.getClass());
    }
  }

  public long actorId(final ActorMention actorMention) {
    switch (this) {
      case PROPER_NOUN: {
        checkState(actorMention instanceof ProperNounActorMention);
        return ((ProperNounActorMention) actorMention).actorID();
      }
      case COMPOSITE: {
        checkState(actorMention instanceof CompositeActorMention);
        return ((CompositeActorMention) actorMention).pairedAgentID();
      }
      case SIMPLE: {
        throw new IllegalArgumentException("Cannot get actor ID for SimpleActorMention");
      }
      default: {
        throw new IllegalArgumentException("Unhandled enum value: " + this);
      }
    }
  }
}
