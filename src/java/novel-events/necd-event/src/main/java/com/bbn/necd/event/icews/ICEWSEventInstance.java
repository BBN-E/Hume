package com.bbn.necd.event.icews;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.wrappers.ICEWSEventMentionInfo;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.theories.actors.ActorMention;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.MoreObjects;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;

import java.io.Serializable;

import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

public final class ICEWSEventInstance implements Serializable {
  private String text;
  private Symbol predicate;
  private ImmutableList<Argument> arguments;
  private ICEWSEventMentionInfo icewsEventMentionInfo;  // since ACCENT only tags a portion of all possible event instances

  @JsonCreator
  private ICEWSEventInstance(
      @JsonProperty("text") final String text,
      @JsonProperty("predicate") final Symbol predicate,
      @JsonProperty("arguments") final ImmutableList<Argument> arguments,
      @JsonProperty("icewseventMentionInfo") final ICEWSEventMentionInfo icewsEventMentionInfo) {
    this.text = checkNotNull(text);
    this.predicate = checkNotNull(predicate);
    this.arguments = checkNotNull(arguments);
    this.icewsEventMentionInfo = icewsEventMentionInfo;
  }

  public static Builder builder(final Proposition prop) {
    return new Builder(prop);
  }

  public String getText() {
    return text;
  }

  public Symbol getPredicate() {
    return predicate;
  }

  public ImmutableList<Argument> getArguments() {
    return arguments;
  }

  public Optional<ICEWSEventMentionInfo> getICEWSEventMentionInfo() {
    return Optional.fromNullable(icewsEventMentionInfo);
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("text", text)
        .add("predicate", predicate)
        .add("arguments", arguments)
        .add("icewsEventMentionInfo", icewsEventMentionInfo)
        .toString();
  }

  public final static class Builder {
    private final Proposition prop;
    private final ImmutableList.Builder<Argument> arguments;
    private ICEWSEventMentionInfo icewsEventMentionInfo = null;

    public Builder(final Proposition prop) {
      checkNotNull(prop);
      checkArgument(prop.predHead().isPresent());
      this.prop = prop;
      this.arguments = ImmutableList.builder();
    }

    public Builder withArgument(final Argument argument) {
      arguments.add(argument);
      return this;
    }

    public Builder withICEWSEventMentionInfo(final ICEWSEventMentionInfo icewsEventMentionInfo) {
      this.icewsEventMentionInfo = icewsEventMentionInfo;
      return this;
    }

    public ICEWSEventInstance build() {
      // We checked this previously so get must succeed
      final SynNode node = prop.predHead().get();
      return new ICEWSEventInstance(prop.span().tokenizedText(), node.terminalSymbols().get(0),
          arguments.build(), icewsEventMentionInfo);
    }
  }

  // we use the interface ActorMention, to leave open possibility of CompositeActorMention (ICEWS) or ProperNounActorMention (AWAKE)
  public final static class Argument implements Serializable {

    private long actorId;
    private Symbol actorName;
    private ActorType actorType;
    private Symbol role;

    // Default constructor to support serialization
    private Argument() {
    }

    public Argument(final long actorId, final Symbol actorName, final Symbol role, final ActorType actorType) {
      this.actorId = actorId;
      this.actorName = actorName;
      this.role = role;
      this.actorType = actorType;
    }

    public static Argument from(final ActorMention actor, final Symbol role) {
      // Cast actor as needed
      final ActorType actorType = ActorType.getType(actor);
      if (ActorType.SIMPLE.equals(actorType)) {
        throw new IllegalArgumentException("Cannot create argument from SimpleActorMention");
      }
      final long actorId = actorType.actorId(actor);
      return new Argument(actorId, actor.actorName().orNull(), role, actorType);
    }

    public long getActorId() {
      return actorId;
    }

    public Optional<Symbol> getActorName() {
      return Optional.fromNullable(actorName);
    }

    public Optional<Symbol> getRole() {
      return Optional.fromNullable(role);
    }

    public ActorType getActorType() {
      return actorType;
    }

    @Override
    public String toString() {
      return MoreObjects.toStringHelper(this)
          .add("actorId", actorId)
          .add("actorName", actorName)
          .add("role", role)
          .toString();
    }
  }

}

