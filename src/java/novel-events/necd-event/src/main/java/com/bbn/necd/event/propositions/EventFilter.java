package com.bbn.necd.event.propositions;

/**
 * Represents filters for events.
 */
public enum EventFilter {
  ALL {
    @Override
    public boolean allowsPath(final PropositionEdge edge) {
      // Allow anything
      return true;
    }

    @Override
    public boolean allowsFilter(EventFilter filter) {
      // Allow anything
      return true;
    }
  },
  SIMPLE {
    @Override
    public boolean allowsPath(final PropositionEdge edge) {
      PropositionRole role = edge.label();
      // Allow only SUBJ, OBJ, and IOBJ
      return role.equals(PropositionRole.SUB_ROLE)
          || role.equals(PropositionRole.OBJ_ROLE)
          || role.equals(PropositionRole.IOBJ_ROLE);
    }

    @Override
    public boolean allowsFilter(EventFilter filter) {
      // Only allow SIMPLE
      return SIMPLE.equals(filter);
    }
  };

  public abstract boolean allowsPath(PropositionEdge edge);

  public abstract boolean allowsFilter(EventFilter filter);
}
