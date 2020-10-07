package com.bbn.serif.util.events.consolidator.proputil;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.nlp.banks.wordnet.IWordNet;
import com.bbn.nlp.banks.wordnet.WordNet;
import com.bbn.nlp.banks.wordnet.WordNetPOS;
import com.bbn.nlp.languages.English;
import com.bbn.nlp.languages.Language;
import com.bbn.nlp.languages.LanguageSpecific;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.List;

import javax.inject.Inject;

import edu.mit.jwi.item.POS;

import static com.google.common.base.Preconditions.checkNotNull;

@LanguageSpecific("English")
public class EnglishWordnetStemmer implements Stemmer {

  private static final Logger log = LoggerFactory.getLogger(EnglishWordnetStemmer.class);

  @Inject
  private EnglishWordnetStemmer(IWordNet wordnet) {
    this.wordnet = checkNotNull(wordnet);
    this.english = English.getInstance();
  }

  public static EnglishWordnetStemmer from(Parameters params) throws IOException {
    return new EnglishWordnetStemmer(WordNet.fromParameters(params));
  }

  // this exists for backwards compatibility.
  // We should establish at some point in the future how good an idea any of this is.
  @LanguageSpecific("English")
  private Optional<Symbol> isDefined(Symbol word, POS wnPOS) {
    // getFirstStemUsingNormalization appears to implement exactly the operation that was previously here
    return wordnet.getFirstStemUsingNormalization(word, WordNetPOS.fromJWIPOS(wnPOS));
  }

  @Override
  @LanguageSpecific("English")
  public Symbol stem(final Symbol word, final Symbol pos) {
    // this method for some, possibly historical, reason prefers to not return a word that is its
    // own stem, so if that is the only option will spend time spinning before giving up and
    // returning the word. This might be a bug.
    final List<Symbol> stemmedWords;
    POS wnPOS = null;
    try {
      if (english.isNominalPOSTag(pos)) {
        stemmedWords = wordnet.getAllStemsForWord(word, WordNetPOS.NOUN);
        wnPOS = POS.NOUN;
      } else if (english.isVerbalPOSExcludingModals(pos)) {
        stemmedWords = wordnet.getAllStemsForWord(word, WordNetPOS.VERB);
        wnPOS = POS.VERB;
      } else {
        stemmedWords = ImmutableList.of();
      }

      if (stemmedWords.isEmpty()) {
        return word;
      } else {
        //make sure the stemmed word is not the same as the original word and also the stemmed word appears in the dictionary
        for (Symbol sw : stemmedWords) {
          if (!sw.equals(word) && isDefined(sw, wnPOS).isPresent()) {
            return sw;
          }
        }

        return word;
      }
    } catch (final IllegalArgumentException iae) {
      log.warn("IllegalArgumentException raised in stemming code for {}/{}; not stemming", word,
          pos);
      return word;
    }
  }


  private final IWordNet wordnet;
  private final Language english;

}
