package com.bbn.necd.event.propositions;

/**
 * Provides an exception for proposition structure problems.
 */
public class PropositionStructureException extends Exception {

  public PropositionStructureException() {
    super();
  }

  public PropositionStructureException(String message) {
    super(message);
  }

  public PropositionStructureException(Throwable cause) {
    super(cause);
  }

  public PropositionStructureException(String message, Throwable cause) {
    super(message, cause);
  }
}
