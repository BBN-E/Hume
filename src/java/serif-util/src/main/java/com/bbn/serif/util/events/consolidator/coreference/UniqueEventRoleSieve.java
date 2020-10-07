package com.bbn.serif.util.events.consolidator.coreference;

import com.bbn.bue.common.symbols.Symbol;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSetMultimap;
import com.google.common.collect.SetMultimap;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;
import java.lang.annotation.Retention;
import java.lang.annotation.Target;

import javax.inject.Qualifier;

import static java.lang.annotation.ElementType.FIELD;
import static java.lang.annotation.ElementType.METHOD;
import static java.lang.annotation.ElementType.PARAMETER;
import static java.lang.annotation.RetentionPolicy.RUNTIME;

//import java.lang.annotation.Target;
//import javax.inject.Qualifier;

//import java.lang.annotation.Retention;

/**
 * Split events to ensure they have unique time and place roles.
 * See #shatterForUniqueRole(SherlockDocument, Symbol, SherlockDocumentEvent)} for details.
 */
//@LanguageSpecific("English")
public final class UniqueEventRoleSieve {
  //private final PlaceContainmentCache placeContainmentCache;
  private final ImmutableSetMultimap<Symbol, Symbol> uniqueEventRoles;

  /*
  private UniqueEventRoleSieve(final PlaceContainmentCache placeContainmentCache,
      @UniqueEventRolesP final SetMultimap<Symbol, Symbol> uniqueEventRoles) {
    this.placeContainmentCache = checkNotNull(placeContainmentCache);
    this.uniqueEventRoles = ImmutableSetMultimap.copyOf(uniqueEventRoles);
  }
  */

  private UniqueEventRoleSieve(final SetMultimap<Symbol, Symbol> uniqueEventRoles) {
    //this.placeContainmentCache = checkNotNull(placeContainmentCache);
    this.uniqueEventRoles = ImmutableSetMultimap.copyOf(uniqueEventRoles);
  }

  /*
  @Override
  Set<SherlockDocumentEvent> siftSingleEventType(final Symbol eventType, final SherlockDocument doc,
      final Set<SherlockDocumentEvent> inputEventFrames) {

    final ImmutableSet.Builder<SherlockDocumentEvent> newEventFrames = ImmutableSet.builder();
    for (final SherlockDocumentEvent ef : inputEventFrames) {
      ImmutableSet<SherlockDocumentEvent> result =
          shatterForUniqueRole(doc, SieveConstants.TIME, ImmutableSet.of(ef));
      result = shatterForUniqueRole(doc, SieveConstants.PLACE, result);
      for (final Symbol uniqueEventRole : uniqueEventRoles.get(eventType)) {
        result = shatterForUniqueRole(doc, uniqueEventRole, result);
      }
      newEventFrames.addAll(result);
    }
    return newEventFrames.build();
  }

  private ImmutableSet<SherlockDocumentEvent> shatterForUniqueRole(final SherlockDocument doc,
      final Symbol role, final ImmutableSet<SherlockDocumentEvent> efs) {

    final ImmutableSet.Builder<SherlockDocumentEvent> ret = ImmutableSet.builder();
    for (final SherlockDocumentEvent ef : efs) {
      ret.addAll(shatterForUniqueRole(doc, role, ef));
    }
    return ret.build();
  }
  */

  /**
   * Certain operations involve the computation of power sets which could be exponentially large.
   * To prevent the program from effectively hanging on pathological input, we specify a maximum
   * size set to compute a power set for
   */
  //private static final int MAX_ARG_SET_SIZE = 12;

  /**
   * Given a document event, potentially splits it into other events to ensure that the given
   * {@code role} does not have multiple fillers within a single document event.
   *
   * In more detail: for a given role, this gathers all subsets (why?) of all filler for this role.
   * Then for each such subset, we make a new event which is the same as the input event, but with
   * only the fillers in that subset acting as fillers for the given {@code role}.  The return
   * value is the set of these new events.
   */
  /*
  private ImmutableSet<SherlockDocumentEvent> shatterForUniqueRole(final SherlockDocument doc,
      final Symbol role, final SherlockDocumentEvent ef) {
    final ImmutableSet.Builder<SherlockDocumentEvent> ret = ImmutableSet.builder();

    final ImmutableSet<SherlockEventArgument> targetEAs = ef.getArgumentsOfEventRole(role);
    final ImmutableSet<SherlockEventArgument> nonTargetEAs = ef.getArgumentsNotOfEventRole(role);

    if (targetEAs.size() <= 1) {
      // there's max of one argument of this role, so we're done as there's no need to split
      return ImmutableSet.of(ef);
    }

    final ImmutableSet<ImmutableSet<SherlockEventArgument>> subsets;

    if (role == SieveConstants.TIME) {
      subsets = TimeRules.getMaximalConsistentSubsets(ef, MAX_ARG_SET_SIZE);
    } else if (role == SieveConstants.PLACE || role == SieveConstants.ORIGIN
        || role == SieveConstants.DESTINATION) {
      subsets = maximalConsistentSubsetsByLocationContainment(doc, role, ef, MAX_ARG_SET_SIZE);
    } else {
      subsets = getMaximalConsistentSubsets(ef.getArgumentsOfEventRole(role), MAX_ARG_SET_SIZE);
    }

    for (final ImmutableSet<SherlockEventArgument> set : subsets) {
      ret.add(SherlockDocumentEvent.builder().eventType(ef.eventType())
          .addAllArguments(nonTargetEAs)
          .addAllArguments(set).derivation(SherlockUtils.deriveFromRuleOnly("UniqueRole"))
          .build());
    }

    return ret.build();
  }
  */

  /**
   * Returns all maximal elements of the partially-ordered set of self-consistent subsets of the
   * input argument set, where self-consistent means the CASes of the arguments do not conflict,
   * where conflicting is defined by not having CompatibleCAS#isCasCompatible(SherlockEventArgument,
   * SherlockEventArgument).
   */
  /*
  private ImmutableSet<ImmutableSet<SherlockEventArgument>> getMaximalConsistentSubsets(
      Set<SherlockEventArgument> args, int maxInputSetSize) {
    final Set<Set<SherlockEventArgument>> subsets =
        SieveUtils.nonEmptySubsetsSafely(args, maxInputSetSize);

    final ImmutableSet.Builder<ImmutableSet<SherlockEventArgument>> fullyContainedSubsetsBuilder =
        ImmutableSet.builder();
    for (final Set<SherlockEventArgument> set : subsets) {
      if (allArgumentsMutuallyCompatible(set)) {
        fullyContainedSubsetsBuilder.add(ImmutableSet.copyOf(set));
      }
    }

    return SieveUtils.discardProperSubsets(fullyContainedSubsetsBuilder.build());
  }

  private boolean allArgumentsMutuallyCompatible(final Set<SherlockEventArgument> set) {
    if (set.size() < 2) {    // singletons are always full contained
      return true;
    } else {
      final ImmutableList<SherlockEventArgument> elements = ImmutableList.copyOf(set);
      for (int i = 0; i < (elements.size() - 1); i++) {
        final SherlockEventArgument arg1 = elements.get(i);
        for (int j = (i + 1); j < elements.size(); j++) {
          final SherlockEventArgument arg2 = elements.get(j);
          if (!CompatibleCAS.isCasCompatible(arg1, arg2) &&
              !SherlockAccessor.hasSameEntity(arg1, arg2)) {
            return false;
          }
        }
      }
      return true;
    }
  }
  */

  @Qualifier
  @Target({FIELD, PARAMETER, METHOD})
  @Retention(RUNTIME)
  public @interface UniqueEventRolesP {

    String param = "sieve.uniqueEventRoles";
  }

  /*
  // location containment code
  private ImmutableSet<ImmutableSet<SherlockEventArgument>> maximalConsistentSubsetsByLocationContainment(
      final SherlockDocument doc, final Symbol role, final SherlockDocumentEvent ef, int maxArgSetSize) {

    final Set<Set<SherlockEventArgument>> subsets =
        SieveUtils.nonEmptySubsetsSafely(ef.getArgumentsOfEventRole(role),
            maxArgSetSize);  // all possible subsets

    final ImmutableSet.Builder<ImmutableSet<SherlockEventArgument>> fullyContainedSubsetsBuilder =
        ImmutableSet.builder();
    for (final Set<SherlockEventArgument> set : subsets) {
      if (allPairwiseContained(placeContainmentCache, doc, set)) {
        fullyContainedSubsetsBuilder.add(ImmutableSet.copyOf(set));
      }
    }

    final ImmutableSet<ImmutableSet<SherlockEventArgument>> fullyContainedSubsets =
        SieveUtils.discardProperSubsets(fullyContainedSubsetsBuilder.build());

    final ImmutableSet.Builder<ImmutableSet<SherlockEventArgument>> ret = ImmutableSet.builder();
    for (final ImmutableSet<SherlockEventArgument> set : fullyContainedSubsets) {
      ret.add(set);
    }
    return ret.build();
  }

  private static boolean allPairwiseContained(PlaceContainmentCache placeContainmentCache,
      final SherlockDocument doc,
      final Set<SherlockEventArgument> set) {
    if (set.size() < 2) {    // singletons are always full contained
      return true;
    } else {
      final ImmutableList<SherlockEventArgument> elements = ImmutableList.copyOf(set);
      for (int i = 0; i < (elements.size() - 1); i++) {
        for (int j = (i + 1); j < elements.size(); j++) {
          if (!placeContainmentCache.hasContainmentRelation(doc, elements.get(i), elements.get(j))) {
            return false;
          }
        }
      }
      return true;
    }
  }
  */

  public static ImmutableSetMultimap<Symbol, Symbol> readUniqueEventRoles(final File infile)
      throws IOException {
    final ImmutableSetMultimap.Builder<Symbol, Symbol> ret = ImmutableSetMultimap.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    for (final String line : lines) {
      final String[] tokens = line.split(" ");
      final Symbol eventType = Symbol.from(tokens[0]);
      final Symbol eventRole = Symbol.from(tokens[1]);
      ret.put(eventType, eventRole);
    }

    return ret.build();
  }
}

