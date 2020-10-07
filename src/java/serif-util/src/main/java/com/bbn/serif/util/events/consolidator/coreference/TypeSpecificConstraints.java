package com.bbn.serif.util.events.consolidator.coreference;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Entity;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Value;
import com.bbn.serif.util.events.consolidator.cas.CanonicalArgumentString;
import com.bbn.serif.util.events.consolidator.cas.CompatibleCAS;
import com.bbn.serif.util.events.consolidator.common.EventCandidate;
import com.bbn.serif.util.events.consolidator.common.PlaceContainmentCache;
import com.bbn.serif.util.events.consolidator.common.PropPathCache;
import com.bbn.serif.util.events.consolidator.common.SieveUtils;
import com.bbn.serif.util.events.consolidator.common.TimeRules;

import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableSetMultimap;
import com.google.common.collect.SetMultimap;

final class TypeSpecificConstraints {

  private final ImmutableSetMultimap<Symbol, Symbol> uniqueEventRoles;
  //private final PropPathCache propPathCache;
  //private final PlaceContainmentCache placeContainmentCache;


  public TypeSpecificConstraints(final SetMultimap<Symbol, Symbol> uniqueEventRoles) {
    this.uniqueEventRoles = ImmutableSetMultimap.copyOf(uniqueEventRoles);
    //this.propPathCache  = checkNotNull(propPathCache);
    //this.placeContainmentCache = checkNotNull(placeContainmentCache);
  }

  boolean conflictsOnLifeMarry(final EventCandidate ef1, final EventCandidate ef2, final DocTheory doc, final CanonicalArgumentString cas) {
    if (ef1.type() != SieveConstants.LIFE_MARRY
        || ef2.type() != SieveConstants.LIFE_MARRY) {
      return false;
    }

    final ImmutableSet<EventMention.Argument> eas1 = ImmutableSet.copyOf(ef1.argsForRole(
        SieveConstants.PERSON));
    final ImmutableSet<EventMention.Argument> eas2 = ImmutableSet.copyOf(ef2.argsForRole(
        SieveConstants.PERSON));

    if (CompatibleCAS.allAreCompatible(eas1, eas2, cas, doc)) {
      return false;
    }

    final ImmutableSet<Entity> entities1 = SieveUtils.getEntities(eas1, doc);
    final ImmutableSet<Entity> entities2 = SieveUtils.getEntities(eas2, doc);

    final ImmutableSet.Builder<Entity> aggregate = ImmutableSet.builder();
    aggregate.addAll(entities1);
    aggregate.addAll(entities2);

    return (aggregate.build().size() > 2);
  }

  boolean conflictsOnBusinessMergeOrg(final EventCandidate e1,
      final EventCandidate e2, final DocTheory doc, final CanonicalArgumentString cas) {
    if (e1.type() != SieveConstants.BUSINESS_MERGE_ORG
        || e2.type() != SieveConstants.BUSINESS_MERGE_ORG) {
      return false;
    }

    final ImmutableSet<EventMention.Argument> eas1 = ImmutableSet.copyOf(e1.argsForRole(
        SieveConstants.ORG));
    final ImmutableSet<EventMention.Argument> eas2 = ImmutableSet.copyOf(e2.argsForRole(
        SieveConstants.ORG));

    if (CompatibleCAS.allAreCompatible(eas1, eas2, cas, doc)) {
      return false;
    }

    final ImmutableSet<Entity> entities1 = SieveUtils.getEntities(eas1, doc);
    final ImmutableSet<Entity> entities2 = SieveUtils.getEntities(eas2, doc);

    final ImmutableSet.Builder<Entity> aggregate = ImmutableSet.builder();
    aggregate.addAll(entities1);
    aggregate.addAll(entities2);

    return (aggregate.build().size() > 2);
  }

  boolean conflictsOnArgumentsForEventRole(final DocTheory doc,
      final EventCandidate e1, final EventCandidate e2, final PlaceContainmentCache placeContainmentCache, final PropPathCache propPathCache, final
      CanonicalArgumentString cas) {
    if (e1.type() != e2.type()) {
      return false;     // there's no conflict if they are with different event type
    }

    final Symbol eventType = e1.type();

    final ImmutableSet.Builder<Symbol> commonEventRoles = ImmutableSet.builder();
    for (final EventMention.Argument ea : e1.arguments()) {
      final Symbol eventRole = ea.role();
      // YS: we make every role unique, to improve Precision of event coreference
      //if (uniqueEventRoles.get(eventType).contains(eventRole) ||
      //    (eventRole == SieveConstants.TIME) || (eventRole == SieveConstants.PLACE)) {
        if (e2.argsForRole(eventRole).size() > 0) {  // record this potential conflict
          commonEventRoles.add(eventRole);
        }
      //}
    }

    boolean hasConflictingTime = false;
    boolean hasConflictingPlace = false;
    boolean hasConflictingEntity = false; // TODO wouldn't this get assigned multiple times below
    boolean hasConflictingValue = false;  // TODO wouldn't this get assigned multiple times below
    for (final Symbol eventRole : commonEventRoles.build()) {
      //System.out.println("Checking on role " + eventRole);

      ImmutableSet<EventMention.Argument> eas1 = e1.argsForRole(eventRole);
      ImmutableSet<EventMention.Argument> eas2 = e2.argsForRole(eventRole);

      /*
      if (eventRole == SieveConstants.PLACE || eventRole == SieveConstants.TIME) {
        eas1 = ImmutableSet.copyOf(e1.argsForRole(eventRole));
        eas2 = ImmutableSet.copyOf(e2.argsForRole(eventRole));
      } else {
        // TODO : should probably not be just using first mention's anchor
        eas1 = propPathCache.discardNonlocalArguments(doc, e1.eventMentions().get(0).anchorNode(), ImmutableSet.copyOf(e1.argsForRole(eventRole)));
        eas2 = propPathCache.discardNonlocalArguments(doc, e2.eventMentions().get(0).anchorNode(), ImmutableSet.copyOf(e2.argsForRole(eventRole)));
      }
      */

      if (eventRole == SieveConstants.TIME) {
        final boolean hasContainment = TimeRules.hasContainmentRelation(eas1, eas2);
        /*
        StringBuilder s1 = new StringBuilder();
        for(final EventMention.Argument arg : eas1) {
          s1.append(arg.span().text().toString());
          s1.append(" ");
        }
        s1.append("vs.");
        for(final EventMention.Argument arg : eas2) {
          s1.append(" ");
          s1.append(arg.span().text().toString());
        }
        System.out.println("hasContainment = " + hasContainment + " ||| " + s1.toString());
        */
        hasConflictingTime = !hasContainment || hasConflictingTime;

        /*
        StringBuilder s = new StringBuilder("");
        for(final Value v : SieveUtils.getValues(eas1)) {
          if(v.timexVal().isPresent()) {
            s.append(v.timexVal().get().asString());
            s.append(" ");
          }
        }
        s.append("vs");
        for(final Value v : SieveUtils.getValues(eas2)) {
          if(v.timexVal().isPresent()) {
            s.append(" ");
            s.append(v.timexVal().get().asString());
          }
        }
        System.out.println("hasConflictingTime " + hasConflictingTime + " " + s.toString());
        */

      } else if (eventRole == SieveConstants.PLACE || eventRole == SieveConstants.ORIGIN
          || eventRole == SieveConstants.DESTINATION) {

        final boolean hasContainment =
            placeContainmentCache.hasContainmentRelation(doc, eas1, eas2);

        /*
        StringBuilder s1 = new StringBuilder();
        for(final EventMention.Argument arg : eas1) {
          s1.append(arg.span().text().toString());
          s1.append(" ");
        }
        s1.append("vs.");
        for(final EventMention.Argument arg : eas2) {
          s1.append(" ");
          s1.append(arg.span().text().toString());
        }
        */

        final boolean areCompatible = CompatibleCAS.allAreCompatible(eas1, eas2, cas, doc);

        //System.out.println("PLACE hasContainment=" + hasContainment + " areCompatible=" + areCompatible + " ||| " + s1.toString());

        hasConflictingPlace = (!hasContainment && !areCompatible) || hasConflictingPlace;
      } else {
        final boolean areCompatible = CompatibleCAS.allAreCompatible(eas1, eas2, cas, doc);

        /*
        StringBuilder s1 = new StringBuilder();
        for (final EventMention.Argument arg : eas1) {
          s1.append(arg.span().text().toString());
          s1.append(" ");
        }
        s1.append("vs.");
        for (final EventMention.Argument arg : eas2) {
          s1.append(" ");
          s1.append(arg.span().text().toString());
        }
        System.out.println("OtherRoles areCompatible=" + areCompatible + " ||| " + s1.toString());
        */

        if (!areCompatible) {
          final ImmutableSet<Entity> entities1 = SieveUtils.getEntities(eas1, doc);
          final ImmutableSet<Entity> entities2 = SieveUtils.getEntities(eas2, doc);

          final ImmutableSet<Value> values1 = SieveUtils.getValues(eas1);
          final ImmutableSet<Value> values2 = SieveUtils.getValues(eas2);

          if (entities1.size() > 0 || entities2.size() > 0) {
            hasConflictingEntity =
                !(entities1.containsAll(entities2) || entities2.containsAll(entities1));
          }
          if (values1.size() > 0 || values2.size() > 0) {
            hasConflictingValue = !(values1.containsAll(values2) || values2.containsAll(values1));
          }

          /*
          StringBuilder s2 = new StringBuilder();
          for (final EventMention.Argument arg : eas1) {
            s2.append(arg.span().text().toString());
            s2.append(" ");
          }
          s2.append("vs.");
          for (final EventMention.Argument arg : eas2) {
            s2.append(" ");
            s2.append(arg.span().text().toString());
          }
          System.out.println("hasConflictEntity=" + hasConflictingEntity + " hasConflictingValue="
              + hasConflictingValue + " ||| " + s2.toString());
          */
        }
      }
    }

    //System.out.println("hasConflictingTime=" + hasConflictingTime + " hasConflictingPlace=" + hasConflictingPlace + " hasConflictingEntity=" + hasConflictingEntity + " hasConflictingValue=" + hasConflictingValue);
    return hasConflictingTime || hasConflictingPlace || hasConflictingEntity || hasConflictingValue;
  }
}

