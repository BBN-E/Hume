package com.bbn.necd.event.propositions;

import com.bbn.necd.common.theory.PropositionPath;
import com.bbn.necd.event.wrappers.ICEWSEventMentionInfo;
import com.bbn.serif.theories.Mention;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;

import static com.google.common.base.Preconditions.checkNotNull;

public class PropositionPathEventInstance {
  private final ImmutableList<Mention> arguments;
  private final PropositionPath propositionPath;
  private final ICEWSEventMentionInfo icewsEventMentionInfo;

  private PropositionPathEventInstance(final ImmutableList<Mention> arguments, final PropositionPath propositionPath,
      final ICEWSEventMentionInfo icewsEventMentionInfo) {
    this.arguments = checkNotNull(arguments);
    this.propositionPath = checkNotNull(propositionPath);
    this.icewsEventMentionInfo = icewsEventMentionInfo;
  }

  public static Builder builder(final Mention argument1, final Mention argument2, final PropositionPath propositionPath) {
    return new Builder(argument1, argument2, propositionPath);
  }

  public ImmutableList<Mention> getArguments() {
    return arguments;
  }

  public PropositionPath getPropositionPath() {
    return propositionPath;
  }

  public Optional<ICEWSEventMentionInfo> getICEWSEventMentionInfo() {
    return Optional.fromNullable(icewsEventMentionInfo);
  }

  public static class Builder {
    private final ImmutableList<Mention> arguments;
    private final PropositionPath propositionPath;
    private ICEWSEventMentionInfo icewsEventMentionInfo = null;

    private Builder(final Mention argument1, final Mention argument2, final PropositionPath propositionPath) {
      checkNotNull(argument1);
      checkNotNull(argument2);
      arguments = ImmutableList.of(argument1, argument2);
      this.propositionPath = checkNotNull(propositionPath);
    }

    public Builder withICEWSEventMentionInfo(final ICEWSEventMentionInfo icewsEventMentionInfo) {
      this.icewsEventMentionInfo = icewsEventMentionInfo;
      return this;
    }

    public PropositionPathEventInstance build() {
      return new PropositionPathEventInstance(arguments, propositionPath, icewsEventMentionInfo);
    }
  }
}
