package com.bbn.necd.event.wrappers;


import com.bbn.serif.theories.actors.ActorMention;

public final class ActorMentionPair {
  private final ActorMention mention1;
  private final ActorMention mention2;

  private ActorMentionPair(final ActorMention mention1, final ActorMention mention2) {
    this.mention1 = mention1;
    this.mention2 = mention2;
  }

  public static ActorMentionPair from(final ActorMention mention1, final ActorMention mention2) {
    return new ActorMentionPair(mention1, mention2);
  }

  public ActorMention getFirstMention() {
    return mention1;
  }

  public ActorMention getSecondMention() {
    return mention2;
  }
}
