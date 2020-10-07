package com.bbn.serif.util.events.consolidator.coreference;

import com.bbn.bue.common.symbols.Symbol;

public final class SieveConstants {

  private SieveConstants() {
    throw new UnsupportedOperationException();
  }

  public final static Symbol TIME = Symbol.from("has_time");
  public final static Symbol PLACE = Symbol.from("has_location");
  public final static Symbol ORIGIN = Symbol.from("has_origin_location");
  public final static Symbol DESTINATION = Symbol.from("has_destination_location");
  public final static Symbol LIFE_MARRY = Symbol.from("Life.Marry");
  public final static Symbol BUSINESS_MERGE_ORG = Symbol.from("Business.Merge-Org");
  public final static Symbol PERSON = Symbol.from("Person");
  public final static Symbol ORG = Symbol.from("Org");
}
