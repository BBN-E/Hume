package com.bbn.necd.event.wrappers;

import com.bbn.necd.common.theory.PropositionPath;
import com.bbn.necd.event.propositions.PropositionPathEventInstance;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.Function;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;

/**
 * Wrap the crucial fields of an {@link PropositionPathEventInstance} for serialization.
 */
public final class EventInstanceInfo {

  private final ImmutableList<MentionInfo> arguments;
  private final PropositionPath propositionPath;
  // While we generally avoid making underlying fields Optional, in this case this we do for
  // ease of serialization.
  private final Optional<ICEWSEventMentionInfo> icewsEventMentionInfo;

  @JsonCreator
  private EventInstanceInfo(
      @JsonProperty("arguments") final ImmutableList<MentionInfo> arguments,
      @JsonProperty("propositionPath") final PropositionPath propositionPath,
      @JsonProperty("icewseventMentionInfo") final Optional<ICEWSEventMentionInfo> icewsEventMentionInfo) {
    this.arguments = arguments;
    this.propositionPath = propositionPath;
    this.icewsEventMentionInfo = icewsEventMentionInfo;
  }

  public static EventInstanceInfo fromEventInstance(final PropositionPathEventInstance eventInstance) {
    final ImmutableList<MentionInfo> mentionInfos =
        ImmutableList.copyOf(Lists.transform(eventInstance.getArguments(), MentionInfo.mentionInfoFromMentionFunction()));
    return new EventInstanceInfo(mentionInfos, eventInstance.getPropositionPath(), eventInstance.getICEWSEventMentionInfo());
  }

  public static Function<PropositionPathEventInstance, EventInstanceInfo> eventInstanceInfoFromEventInstanceFunction() {
    return EventInstanceInfoFromEventInstanceFunction.INSTANCE;
  }

  public ImmutableList<MentionInfo> getArguments() {
    return arguments;
  }

  public PropositionPath getPropositionPath() {
    return propositionPath;
  }

  public Optional<ICEWSEventMentionInfo> getICEWSEventMentionInfo() {
    return icewsEventMentionInfo;
  }

  private enum EventInstanceInfoFromEventInstanceFunction implements Function<PropositionPathEventInstance, EventInstanceInfo> {
    INSTANCE;

    @Override
    public EventInstanceInfo apply(final PropositionPathEventInstance eventInstance) {
      return fromEventInstance(eventInstance);
    }
  }
}
