package com.bbn.serif.util.events.consolidator.common;

//import static com.bbn.kbp.events2014.place.PlaceContainmentUtils.findPopulatedLocationRecords;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.geonames.GeoNames;
import com.bbn.bue.geonames.GeonamesException;
import com.bbn.bue.geonames.LocationRecord;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Entity;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.RelationMention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.cas.CanonicalArgumentString;
import com.bbn.serif.util.place.PlaceContainmentUtils;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;

import org.apache.commons.lang3.StringUtils;

import java.util.Collection;

public final class PlaceContainmentCache {
  //private final GeoNames geonames;
  private final CanonicalArgumentString cas;



  //public static PlaceContainmentCache from(final GeoNames geonames) {
  //  return new PlaceContainmentCache(g);
  //}


  private final static Symbol PLACE = Symbol.from("Place");
  private final static Symbol PARTWHOLE_GEOGRAPHICAL = Symbol.from("PART-WHOLE.Geographical");
  private final static Symbol PHYS_LOCATED = Symbol.from("PHYS.Located");

  private final PlaceContainmentKnowledge placeContainmentKnowledge;

  //public PlaceContainmentCache(final GeoNames geonames, final CanonicalArgumentString cas, final PlaceContainmentKnowledge placeContainmentKnowledge) {
  //  this.geonames = geonames;
  //  this.cas = cas;
  //  this.placeContainmentKnowledge = placeContainmentKnowledge;
  //}

  public PlaceContainmentCache(final GeoNames geonames, final CanonicalArgumentString cas, final DocTheory doc) throws GeonamesException {
    //this.geonames = geonames;
    this.cas = cas;
    this.placeContainmentKnowledge = constructPlaceContainmentKnowledge(doc, geonames);
  }

  /*
  private final LoadingCache<SherlockDocument, PlaceContainmentKnowledge> placeKnowledgePerDoc =
      CacheBuilder.newBuilder().maximumSize(5).build(
          new CacheLoader<SherlockDocument, PlaceContainmentKnowledge>() {
            @Override
            public PlaceContainmentKnowledge load(final SherlockDocument doc) throws Exception {
              final Optional<PlaceContainmentKnowledge> placeKnowledge;
              placeKnowledge = Optional.of(constructPlaceContainmentKnowledge(doc));
              checkState(placeKnowledge.isPresent());
              return placeKnowledge.get();
            }
          });

  @Inject
  PlaceContainmentCache(@GeonamesForKBPP GeoNames geonames) {
    this.geonames = checkNotNull(geonames);
  }
  */


  public boolean hasContainmentRelation(final DocTheory doc,
      final ImmutableSet<EventMention.Argument> args1,
      final ImmutableSet<EventMention.Argument> args2) {

    for (final EventMention.Argument arg1 : args1) {
      for (final EventMention.Argument arg2 : args2) {
        if (!hasContainmentRelation(doc, arg1, arg2)) {
          return false;
        }
      }
    }

    return true;
  }

  /*
  private PlaceContainmentKnowledge getPlaceKnowledge(DocTheory doc) {
    try {
      return placeKnowledgePerDoc.get(doc);
    } catch (ExecutionException e) {
      throw new SerifException(e);
    }
  }
  */

  private PlaceContainmentKnowledge constructPlaceContainmentKnowledge(final DocTheory doc, final GeoNames geonames)
      throws GeonamesException {

    final ImmutableSet<EventMention.Argument> placeArguments = getPlaceArguments(doc);
    final ImmutableSet<String> placeBfStrings = getBFStringsOfNameArguments(placeArguments);
    final ImmutableSet<String> placeCASStrings = getCASStrings(placeArguments, doc);

    // get GeoNames Location records for all the above Place strings
    final ImmutableSet.Builder<LocationRecord> locationRecordsBuilder = ImmutableSet.builder();
    for (final String placeString : placeBfStrings) {
      locationRecordsBuilder.addAll(PlaceContainmentUtils.findPopulatedLocationRecords(geonames, placeString));
    }
    for (final String placeString : placeCASStrings) {
      locationRecordsBuilder.addAll(PlaceContainmentUtils.findPopulatedLocationRecords(geonames, placeString));
    }
    final ImmutableSet<LocationRecord> locationRecords = locationRecordsBuilder.build();

    // Knowledge: construct Place containment based on the Place arguments in this doc.
    // In the multimap: child-parent
    final ImmutableMultimap<String, String> placeContainmentStrings =
        constructPlaceContainmentStringMap(locationRecords);

    // Knowledge: based on Relation PARTWHOLE_GEOGRAPHICAL
    final ImmutableMultimap<Mention, Mention> placeContainmentMentions =
        constructPlaceContainmentMentionMap(doc);

    // Knowledge: based on Relation PHYS_LOCATED.
    // The Mentions in each ImmutableSet<Mention> are assumed to be inherently compatible
    final ImmutableSet<ImmutableSet<Mention>> locatedMentions = constructLocatedMentions(doc);

    return new PlaceContainmentKnowledge(placeContainmentStrings, placeContainmentMentions,
        locatedMentions);
  }

  private ImmutableSet<EventMention.Argument> getPlaceArguments(final DocTheory doc) {

    final ImmutableSet.Builder<EventMention.Argument> ret = ImmutableSet.builder();
    for(int sentenceIndex=0; sentenceIndex<doc.numSentences(); sentenceIndex++) {
      for(final EventMention em : doc.sentenceTheory(sentenceIndex).eventMentions()) {
        for(final EventMention.Argument arg : em.arguments()) {
          if(arg.role() == PLACE) {
            ret.add(arg);
          }
        }
      }
    }
    return ret.build();
  }

  private ImmutableSet<String> getBFStringsOfNameArguments(
final ImmutableSet<EventMention.Argument> args) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();
    for (final EventMention.Argument arg : args) {
      final Optional<Mention> mention = SieveUtils.getEntityMention(arg);
      if (mention.isPresent()) {
        if (mention.get().mentionType() == Mention.Type.NAME) {
          ret.add(mention.get().span().tokenizedText().utf16CodeUnits());
        }
      }
    }
    return ret.build();
  }

  private ImmutableSet<String> getCASStrings(final ImmutableSet<EventMention.Argument> args, final DocTheory doc) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();
    for (final EventMention.Argument arg : args) {
      final Optional<String> casString = cas.getCASString(arg, doc);
      if(casString.isPresent()) {
        ret.add(casString.get());
      }
    }
    return ret.build();
  }

  private ImmutableMultimap<Mention, Mention> constructPlaceContainmentMentionMap(
      final DocTheory doc) {

    final ImmutableMultimap.Builder<Mention, Mention> ret = ImmutableMultimap.builder();
    for (final SentenceTheory st : doc.nonEmptySentenceTheories()) {
      for (final RelationMention rm : st.relationMentions()) {
        if (rm.type() == PARTWHOLE_GEOGRAPHICAL) {
          final Mention arg1 = rm.leftMention();
          final Mention arg2 = rm.rightMention();
          ret.put(arg1, arg2);
        }
      }
    }
    return ret.build();
  }

  private ImmutableSet<ImmutableSet<Mention>> constructLocatedMentions(
      final DocTheory doc) {

    final ImmutableMultimap.Builder<Mention, Mention> mentionMap = ImmutableMultimap.builder();
    for (final SentenceTheory st : doc.nonEmptySentenceTheories()) {
      for (final RelationMention rm : st.relationMentions()) {
        if (rm.type() == PHYS_LOCATED) {
          final Mention arg1 = rm.leftMention();
          final Mention arg2 = rm.rightMention();
          mentionMap.put(arg1, arg2);
        }
      }
    }

    final ImmutableSet.Builder<ImmutableSet<Mention>> ret = ImmutableSet.builder();
    for (final Collection<Mention> mentions : mentionMap.build().asMap().values()) {
      if (mentions.size() > 1) {
        ret.add(ImmutableSet.copyOf(mentions));
      }
    }
    return ret.build();
  }


  private ImmutableMultimap<String, String> constructPlaceContainmentStringMap(
      final ImmutableSet<LocationRecord> records) {
    final ImmutableMultimap.Builder<String, String> ret = ImmutableMultimap.builder();
    for (final LocationRecord record : records) {
      ret.putAll(PlaceContainmentUtils.constructPlaceContainmentMap(record));
    }
    return ret.build();
  }

  // uses the following pieces of information:
  // - whether they coref to the same entity
  // - whether their CAS are the same
  // - geoNames
  // - relation prediction of PART-WHOLE.Geographical
  // - relation prediction of PHYS.Located
  public boolean hasContainmentRelation(final DocTheory doc,
      final EventMention.Argument arg1, final EventMention.Argument arg2) {

    // In general, GPE should not be compatible with LOC
    final Optional<Mention> m1 = SieveUtils.getEntityMention(arg1);
    final Optional<Mention> m2 = SieveUtils.getEntityMention(arg2);
    if(m1.isPresent() && m2.isPresent()) {
      final String et1 = m1.get().entityType().name().asString();
      final String et2 = m2.get().entityType().name().asString();
      if( (et1.compareTo("GPE")==0 && et2.compareTo("LOC")==0) ||
          (et1.compareTo("LOC")==0 && et2.compareTo("GPE")==0) ) {
        return false;
      }
    }

    final PlaceContainmentKnowledge placeKnowledge = this.placeContainmentKnowledge;

    final Optional<Entity> entity1 = SieveUtils.getEntity(arg1, doc);
    final Optional<Entity> entity2 = SieveUtils.getEntity(arg2, doc);

    if (entity1.isPresent() && entity2.isPresent() && entity1.get() == entity2.get()) {
      return true;
    }

    // TODO: check whether getCASString returns a non absent value
    final Optional<String> arg1Cas = cas.getCASString(arg1, doc);
    final Optional<String> arg2Cas = cas.getCASString(arg2, doc);
    if(!arg1Cas.isPresent() || !arg2Cas.isPresent()) {
      return false;
    }

    final String arg1CASString = StringUtils.lowerCase(arg1Cas.get());
    final String arg2CASString = StringUtils.lowerCase(arg2Cas.get());
    if (arg1CASString.equals(arg2CASString)) {
      return true;
    }

    if (placeKnowledge.contains(arg1CASString, arg2CASString) ||
        placeKnowledge.contains(arg2CASString, arg1CASString)) {
      return true;
    }


    if (!m1.isPresent() || !m2.isPresent()) {
      return false;
    }

    if (placeKnowledge.contains(m1.get(), m2.get()) || placeKnowledge.contains(m2.get(), m1.get())) {
      return true;
    }

    if (placeKnowledge.located(m1.get(), m2.get())) {
      return true;
    }

    final Optional<String> m1Text = SieveUtils.getEntityMentionText(arg1);
    final Optional<String> m2Text = SieveUtils.getEntityMentionText(arg2);

    final boolean eitherLacksMentionText = !m1Text.isPresent() || !m2Text.isPresent();
    if (eitherLacksMentionText) {
      return false;
    }

    return placeKnowledge.contains(m1Text.get(), m2Text.get()) ||
        placeKnowledge.contains(m2Text.get(), m1Text.get());
  }

  private static final class PlaceContainmentKnowledge {

    private final ImmutableMultimap<String, String> containmentStrings;
    private final ImmutableMultimap<Mention, Mention> containmentMentions;
    private final ImmutableSet<ImmutableSet<Mention>> locatedMentions;

    private PlaceContainmentKnowledge(final ImmutableMultimap<String, String> containmentStrings,
        final ImmutableMultimap<Mention, Mention> containmentMentions,
        final ImmutableSet<ImmutableSet<Mention>> locatedMentions) {
      this.containmentStrings = containmentStrings;
      this.containmentMentions = containmentMentions;
      this.locatedMentions = locatedMentions;
    }

    // does s1 contain s2
    private boolean contains(final String s1, final String s2) {
      return containmentStrings.containsEntry(StringUtils.lowerCase(s2), StringUtils.lowerCase(s1));
    }

    // does m1 contain m2
    private boolean contains(final Mention m1, final Mention m2) {
      return containmentMentions.containsEntry(m2, m1);
    }

    // does m1 and m2 have a located relation
    private boolean located(final Mention m1, final Mention m2) {
      for (final ImmutableSet<Mention> set : locatedMentions) {
        if (set.contains(m1) && set.contains(m2)) {
          return true;
        }
      }
      return false;
    }
  }


}
