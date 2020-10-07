package com.bbn.serif.util.events.consolidator.coreference;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.geonames.GeoNames;
import com.bbn.bue.geonames.GeonamesException;
import com.bbn.nlp.languages.English;
import com.bbn.nlp.languages.Language;
import com.bbn.serif.util.events.consolidator.proputil.EnglishWordnetStemmer;
import com.bbn.serif.util.events.consolidator.proputil.Stemmer;
import com.bbn.serif.util.events.consolidator.cas.CanonicalArgumentString;
import com.bbn.serif.util.events.consolidator.cas.KBPRepresentativeMentionStrategy;
import com.bbn.serif.util.events.consolidator.common.SieveUtils;

import com.google.common.collect.ImmutableSetMultimap;

import java.io.IOException;

public class SieveKnowledge {
  private final Language language;
  private final Stemmer stemmer;
  private final Connectives connectives;
  //private final PlaceContainmentCache placeContainmentCache;
  private final TypeSpecificConstraints typeSpecificConstraints;
  private final GeoNames geonames;
  private final CanonicalArgumentString cas;

  private SieveKnowledge(final Language language, final Stemmer stemmer, final Connectives connectives, final TypeSpecificConstraints typeSpecificConstraints, final GeoNames geonames, final CanonicalArgumentString cas) {
    this.language = language;
    this.stemmer = stemmer;
    this.connectives = connectives;
    //this.placeContainmentCache = placeContainmentCache;
    this.typeSpecificConstraints = typeSpecificConstraints;
    this.geonames = geonames;
    this.cas = cas;
  }

  public static SieveKnowledge from(final Parameters params)
      throws IOException, GeonamesException, ClassNotFoundException {
    final Language language = English.getInstance();
    final Stemmer stemmer = EnglishWordnetStemmer.from(params);

    final Connectives connectives = Connectives.from(params);

    //final PropPathCache propPathCache = new PropPathCache(language, stemmer);

    final GeoNames geonames = SieveUtils.getGeonames(params);
    final CanonicalArgumentString
        cas = new CanonicalArgumentString(KBPRepresentativeMentionStrategy.createFromParameters(params));
    //final PlaceContainmentCache placeContainmentCache = new PlaceContainmentCache(geonames, cas);

    final ImmutableSetMultimap<Symbol, Symbol> uniqueEventRoles = UniqueEventRoleSieve.readUniqueEventRoles(params.getExistingFile("sieve.uniqueEventRoles"));
    final TypeSpecificConstraints typeSpecificConstraints = new TypeSpecificConstraints(uniqueEventRoles);

    return new SieveKnowledge(language, stemmer, connectives, typeSpecificConstraints, geonames, cas);
  }

  public Language language() {
    return this.language;
  }

  public Stemmer stemmer() {
    return this.stemmer;
  }

  public Connectives connectives() {
    return this.connectives;
  }

  //public PlaceContainmentCache placeContainmentCache() {
  //  return this.placeContainmentCache;
  //}

  public TypeSpecificConstraints typeSpecificConstraints() {
    return this.typeSpecificConstraints;
  }

  //public void loadDocument(final DocTheory doc) throws GeonamesException {
  //  this.placeContainmentCache.loadDocument(doc);
  //}

  public GeoNames geonames() {
    return this.geonames;
  }

  public CanonicalArgumentString cas() {
    return this.cas;
  }

}
