package com.bbn.necd.event.wrappers;

import com.bbn.necd.event.icews.ActorType;
import com.bbn.serif.theories.actors.ActorMention;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.MoreObjects;

import static com.bbn.bue.common.StringUtils.SpaceJoiner;

/**
 * Wrap the crucial fields of a {@link com.bbn.serif.theories.actors.ActorMention} for serialization.
 */
public final class ActorMentionInfo {

  private final MentionInfo mention;
  private final long actorId;
  private final ActorType actorType;

  private ActorMentionInfo(
      @JsonProperty("mention") MentionInfo mention,
      @JsonProperty("actorId") final long actorId,
      @JsonProperty("actorType") final ActorType actorType) {
    this.mention = mention;
    this.actorId = actorId;
    this.actorType = actorType;
  }

  public static ActorMentionInfo from(final ActorMention actorMention) {
    final MentionInfo mentionInfo = MentionInfo.from(actorMention.mention());
    final ActorType actorType = ActorType.getType(actorMention);
    final long actorId = actorType.actorId(actorMention);
    return new ActorMentionInfo(mentionInfo, actorId, actorType);
  }

  public MentionInfo getMention() {
    return mention;
  }

  public long getActorId() {
    return actorId;
  }

  public ActorType getActorType() {
    return actorType;
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("mention", mention)
        .add("actorId", actorId)
        .add("actorType", actorType)
        .toString();
  }

  public String prettyPrint() {
    return SpaceJoiner.join(mention.getTokens()) + " (" + actorId + ")";
  }
}
