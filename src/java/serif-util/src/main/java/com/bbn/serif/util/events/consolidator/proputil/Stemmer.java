package com.bbn.serif.util.events.consolidator.proputil;

import com.bbn.bue.common.symbols.Symbol;

public interface Stemmer {

  Symbol stem(Symbol word, Symbol POS);
}


