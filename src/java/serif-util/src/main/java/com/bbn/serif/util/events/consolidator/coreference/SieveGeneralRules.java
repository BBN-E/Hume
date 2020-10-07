package com.bbn.serif.util.events.consolidator.coreference;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.util.events.consolidator.common.EventCandidate;
import com.bbn.serif.util.events.consolidator.common.SieveUtils;

import com.google.common.collect.ImmutableSet;

public final class SieveGeneralRules {

  /*
  public static boolean conflictsOnRealis(final SherlockDocumentEvent ef1,
      final SherlockDocumentEvent ef2) {
    final ImmutableSet<Symbol> realis1 = SieveUtils.realis(ef1);
    final ImmutableSet<Symbol> realis2 = SieveUtils.realis(ef2);

    return ( (realis1.contains(SieveUtils.GENERIC) && (realis2.contains(SieveUtils.ACTUAL) || realis2.contains(SieveUtils.OTHER))) ||
                 (realis2.contains(SieveUtils.GENERIC) && (realis1.contains(SieveUtils.ACTUAL) || realis1.contains(SieveUtils.OTHER))) );
  }
  */

  public static boolean conflictsOnAnchorPostag(final EventCandidate ef1,
      final EventCandidate ef2) {
    final ImmutableSet<Symbol> postags1 = ef1.getAnchorPostags();
    final ImmutableSet<Symbol> postags2 = ef2.getAnchorPostags();

    return ((postags1.contains(SieveUtils.NN) && postags2.contains(SieveUtils.NNS)) ||
                (postags1.contains(SieveUtils.NNS) && postags2.contains(SieveUtils.NN)) );
  }

}
