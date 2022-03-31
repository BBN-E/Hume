package com.bbn.serif.util.resolver;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.parameters.Parameters;

import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.io.SerifXMLWriter;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.documentresolver.*;
import com.bbn.serif.util.resolver.eventmentionresolver.*;
import com.bbn.serif.util.resolver.sentenceresolver.*;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMap;

import java.io.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class DocTheoryResolver {

    public static ImmutableMap<String, OntologyHierarchy> getMapOfOntologies(final Map<String, Object> persistentObjects) {
        final ImmutableMap.Builder<String, OntologyHierarchy> ret = ImmutableMap.builder();

        for (final Object obj : persistentObjects.values()) {
            if (obj instanceof OntologyHierarchy) {
                final OntologyHierarchy oh = (OntologyHierarchy) obj;
                ret.put(oh.getOntologyName(), oh);
            }
        }

        return ret.build();
    }

    final Parameters params ;
    final List<Resolver> resolvers;
    public DocTheoryResolver(Parameters params) throws Exception {
        this.params = params;
        // Load persistent objects which can exists across resolvers
        final Optional<List<String>> persistentObjectNamesOpt = params.getOptionalStringList("persistentObjects");
        Map<String, Object> persistentObjects = new HashMap<>();

        List<String> persistentObjectNames = new ArrayList<>();
        if (persistentObjectNamesOpt.isPresent())
            persistentObjectNames = persistentObjectNamesOpt.get();

        for (String name : persistentObjectNames) {
            switch (name) {
                case "EventOntologyHierarchy":
                    String roleOntologyFile = params.getString("EventOntologyHierarchy.roleOntologyFile");
                    String yamlOntologyFile = params.getString("EventOntologyHierarchy.yamlOntologyFile");
                    String argumentRoleEntityTypeFile =
                            params.getString("EventOntologyHierarchy.argumentRoleEntityTypeFile");
                    String keywordFile = params.getString("EventOntologyHierarchy.keywordFile");
                    String lemmaFile = params.getString("EventOntologyHierarchy.lemmaFile");
                    String blacklistFile = params.getString("EventOntologyHierarchy.blacklistFile");

                    persistentObjects.put("EventOntologyHierarchy",
                            new OntologyHierarchy(OntologyHierarchy.INTERNAL_ONTOLOGY, roleOntologyFile, yamlOntologyFile, argumentRoleEntityTypeFile,
                                    keywordFile, lemmaFile, blacklistFile));
                    break;
                case "CFOntologyHierarchy":
                    roleOntologyFile = params.getString("CFOntologyHierarchy.roleOntologyFile");
                    yamlOntologyFile = params.getString("CFOntologyHierarchy.yamlOntologyFile");
                    argumentRoleEntityTypeFile =
                            params.getString("CFOntologyHierarchy.argumentRoleEntityTypeFile");
                    keywordFile = params.getString("CFOntologyHierarchy.keywordFile");
                    lemmaFile = params.getString("CFOntologyHierarchy.lemmaFile");
                    blacklistFile = params.getString("CFOntologyHierarchy.blacklistFile");

                    persistentObjects.put("CFOntologyHierarchy",
                            new OntologyHierarchy(OntologyHierarchy.CAUSAL_FACTOR_ONTOLOGY, roleOntologyFile, yamlOntologyFile, argumentRoleEntityTypeFile,
                                    keywordFile, lemmaFile, blacklistFile));
                    break;
                default:
                    throw new Exception("Unknown persistentObject: " + name);
            }
        }

        // Initialize resolvers
        System.out.println("Initializing resolvers");
        final List<String> resolverNames = params.getStringList("resolvers");
        this.resolvers = new ArrayList<>();
        for (String name : resolverNames) {
            switch (name) {

                case "ClearEventsResolver":
                    resolvers.add(new ClearEventsResolver());
                    break;

                case "EventMentionAnchorPhraseResolver":
                    resolvers.add(new EventMentionAnchorPhraseResolver());
                    break;

                case "LabelEventMentionWithModelResolver":
                    // Need KBP file to figure out what events are NN or KBP
                    String kbpEventMappingFile1 =
                            params.getString("LabelEventMentionWithModelResolver.kbpEventMappingFile");
                    resolvers.add(new LabelEventMentionWithModelResolver(
                            getMapOfOntologies(persistentObjects), kbpEventMappingFile1));
                    break;

                case "MapAccentEventMentionResolver":
                    String accentEventMapFile =
                            params.getString("MapAccentEventMentionResolver.accentEventMapFile");
                    String cameoCodeToEventTypeFile = params.getString(
                            "MapAccentEventMentionResolver.cameoCodeToEventTypeFile");
                    resolvers.add(new MapAccentEventMentionResolver(
                            (OntologyHierarchy) persistentObjects.get("EventOntologyHierarchy"),
                            accentEventMapFile, cameoCodeToEventTypeFile));
                    break;

                case "KeywordEventMentionRemover":
                    String adverbsFile = params.getString("KeywordEventMentionRemover.adverbsFile");
                    String prepositionsFile =
                            params.getString("KeywordEventMentionRemover.prepositionsFile");
                    String verbsFile = params.getString("KeywordEventMentionRemover.verbsFile");
                    resolvers.add(new KeywordEventMentionRemover(
                            getMapOfOntologies(persistentObjects), adverbsFile, prepositionsFile, verbsFile));
                    break;

                case "KBPEventMentionConverter":
                    String kbpEventMappingFile2 =
                            params.getString("KBPEventMentionConverter.kbpEventMappingFile");
                    resolvers.add(new KBPEventMentionConverter(getMapOfOntologies(persistentObjects), kbpEventMappingFile2));
                    break;

                case "NNEventMentionConverter":
                    resolvers.add(new NNEventMentionConverter(getMapOfOntologies(persistentObjects)));
                    break;

                case "InterventionEventResolver":
                    String interventionJson =
                            params.getString("InterventionEventResolver.interventionJson");
                    resolvers.add(new InterventionEventResolver(
                            (OntologyHierarchy) persistentObjects.get("EventOntologyHierarchy"),
                            interventionJson));
                    break;

                case "GenericEventMentionConverter":
                    resolvers.add(new GenericEventMentionConverter(getMapOfOntologies(persistentObjects)));
                    break;

                case "KeywordEventMentionAdder":
                    resolvers.add(new KeywordEventMentionAdder(getMapOfOntologies(persistentObjects)));
                    break;

                case "AccentEventMentionMerger":
                    resolvers.add(new AccentEventMentionMerger(getMapOfOntologies(persistentObjects)));
                    break;

                case "KBPEventMentionMerger":
                    resolvers.add(new KBPEventMentionMerger(getMapOfOntologies(persistentObjects)));
                    break;

                case "NNEventMentionMerger":
                    resolvers.add(new NNEventMentionMerger(getMapOfOntologies(persistentObjects)));
                    break;

                case "GenericEventMentionMerger":
                    resolvers.add(new GenericEventMentionMerger(
                            (OntologyHierarchy) persistentObjects.get("EventOntologyHierarchy")));
                    break;

                case "AllEventMentionMerger":
                    resolvers.add(new AllEventMentionMerger(getMapOfOntologies(persistentObjects)));
                    break;

                case "TimeArgumentAdder":
                    resolvers.add(new TimeArgumentAdder());
                    break;

                case "PlaceArgumentAdder":
                    resolvers.add(new PlaceArgumentAdder());
                    break;

                case "ThemeArgumentAdder":
                    String invalidThemeTypes = params.getString("ThemeArgumentAdder.invalidThemeTypes");
                    String validFactorTypes = params.getString("ThemeArgumentAdder.validFactorTypes");
                    String selectionConstraints = params.getString("ThemeArgumentAdder.selectionConstraints");
                    resolvers.add(new ThemeArgumentAdder(invalidThemeTypes, validFactorTypes, selectionConstraints));
                    break;

                case "PropertyArgumentAdder":
                    String propertyPropertyTypes = params.getString("PropertyArgumentAdder.propertyTypes");
                    String propertyProcessTypes = params.getString("PropertyArgumentAdder.processTypes");
                    //String propertySelectionConstraints = params.getString("PropertyArgumentAdder.selectionConstraints");
                    //resolvers.add(new ThemeArgumentAdder(invalidPropertyTypes, propertyValidFactorTypes, propertySelectionConstraints));
                    resolvers.add(new PropertyArgumentAdder(propertyProcessTypes, propertyPropertyTypes));
                    break;

                case "ActorArgumentAdder":
                    String metadataFile = params.getString("ActorArgumentAdder.metadataFile");
                    resolvers.add(new ActorArgumentAdder(metadataFile));
                    break;

                case "ArtifactArgumentAdder":
                    List<String> subtypesToAddAsArguments =
                            params.getStringList("ArtifactArgumentAdder.subtypes");
                    resolvers.add(new ArtifactArgumentAdder(subtypesToAddAsArguments));
                    break;

                case "PruneOverlappingArgumentResolver":
                    resolvers.add(new PruneOverlappingArgumentResolver());
                    break;

                case "PruneBlacklistResolver":
                    resolvers.add(new PruneBlacklistResolver(getMapOfOntologies(persistentObjects)));
                    break;

                case "PruneArgumentsByEntityTypeResolver":
                    resolvers.add(new PruneArgumentsByEntityTypeResolver());
                    break;

                case "EventMentionDirectionOfChangeResolver":
                    String propertiesFile =
                            params.getString("EventMentionDirectionOfChangeResolver.propertiesFile");
                    resolvers.add(new EventMentionDirectionOfChangeResolver(propertiesFile));
                    break;
                case "EventDirectionOfChangeAndCFTrendResolver":
                    resolvers.add(new EventDirectionOfChangeAndCFTrendResolver(params.getString("EventDirectionOfChangeAndCFTrendResolver.propertiesFile")));
                    break;
                case "LightVerbsEventMentionAdder":
                    String lightVerbsFile =
                            params.getString("LightVerbsEventMentionAdder.lightVerbsFile");
                    resolvers.add(new LightVerbsEventMentionAdder(lightVerbsFile));
                    break;
                case "EventEventRelationPolarityResolver":
                    String negationFile =
                            params.getString("EventEventRelationPolarityResolver.negation_file");
                    resolvers.add(new EventEventRelationPolarityResolver(negationFile));
                    break;
                case "EventEventRelationRationaleResolver":
                    String relationDirectory =
                            params.getString("EventEventRelationRationaleResolver.word_list");
                    resolvers.add(new EventEventRelationRationaleResolver(relationDirectory));
                    break;
                case "AttachCorefLightAnchorResolver":
                    String lightWordsFile =
                            params.getString("AttachCorefLightAnchorResolver.lightWordsFile");
                    resolvers.add(new AttachCorefLightAnchorResolver(lightWordsFile));
                    break;

                case "EventMentionSemanticPhraseGrouper":
                    resolvers.add(new EventMentionSemanticPhraseGrouper(params.getString("LightVerbsEventMentionAdder.lightVerbsFile")));
                    break;

                case "ConstrainToEventOntologyResolver":
                    resolvers.add(new ConstrainToEventOntologyResolver(getMapOfOntologies(persistentObjects)));
                    break;

                case "PropagateEventMentionArgumentResolver":
                    int copyArgumentSentenceWindow =
                            params.getInteger(
                                    "PropagateEventMentionArgumentResolver.copyArgumentSentenceWindow");
                    resolvers.add(new PropagateEventMentionArgumentResolver(copyArgumentSentenceWindow));
                    break;

                case "SimpleEventCreator":
                    resolvers.add(new SimpleEventCreator());
                    break;

                case "SimpleEntityCreator":
                    resolvers.add(new SimpleEntityCreator());
                    break;

                case "EventFactorMagnitudeResolver":
                    String factorPropertiesFile =
                            params.getString("EventFactorMagnitudeResolver.propertiesFile");
                    String reverseFactorTypesFile =
                            params.getString("EventFactorMagnitudeResolver.reverseFactorTypesFile");
                    resolvers.add(new EventFactorMagnitudeResolver(
                            factorPropertiesFile, reverseFactorTypesFile));
                    break;
                case "MoveAllEventTypesToCausalFactorTypesResolver":
                    resolvers.add(new MoveAllEventTypesToCausalFactorTypesResolver());
                    break;
                case "FlipOppositeCFToPositiveResolver":
                    String CFTypeMappingFile = params.getString("FlipOppositeCFToPositiveResolver.pendingFlippingOppositeTypeMap");
                    resolvers.add(new FlipOppositeCFToPositiveResolver(CFTypeMappingFile));
                    break;
                case "EventEventRelationReAttachResolver":
                    resolvers.add(new EventEventRelationReAttachResolver());
                    break;
                case "StandaloneGenericEventPruner":
                    resolvers.add(new StandaloneGenericEventPruner());
                    break;
                case "EventConfidenceCalibrationResolver":
                    resolvers.add(new EventConfidenceCalibrationResolver());
                    break;
                case "EventFactorKeywordConfidenceResolver":
                    String weightFile = params.getString("EventFactorKeywordConfidenceResolver.weightFile");
                    resolvers.add(new EventFactorKeywordConfidenceResolver(weightFile));
                    break;
                case "PropertyAsValueMentionResolver":
                    resolvers.add(new PropertyAsValueMentionResolver());
                    break;
                case "TrendEventDropper":
                    resolvers.add(new TrendEventDropper());
                    break;
                case "EventMentionTypeResolver":
                    resolvers.add(new EventMentionTypeResolver());
                    break;
                case "AnchorEventMentionMerger":
                    resolvers.add(new AnchorEventMentionMerger());
                    break;
                case "PatternPruner":
                    String patternFile = params.getString("PatternPruner.patternFile");
                    int eventContextSize = params.getInteger("PatternPruner.eventContextWindowSize");
                    Optional<Integer> maxEERDistance = params.getOptionalInteger("PatternPruner.maxEERTokenDistance");
                    resolvers.add(new PatternPruner(patternFile, eventContextSize, maxEERDistance));
                    break;
                case "EventTypeOntologyComplianceResolver":
                    resolvers.add(new EventTypeOntologyComplianceResolver(params.getStringList("eventOntologyFiles")));
                    break;
                case "ExternalGenericEventRemover":
                    resolvers.add(new ExternalGenericEventRemover(params.getStringList("ExternalGenericEventRemover.eventOntologyFiles")));
                    break;
                default:
                    throw new Exception("Unknown resolver: " + name);
            }
        }
        System.out.println("Done Initializing resolvers");
    }

    public DocTheory resolve(DocTheory docTheory){

            DocTheory newDT = docTheory.modifiedCopyBuilder().build();

            for (Resolver resolver : this.resolvers) {
                System.out.println("Applying resolver "+resolver.getClass().getSimpleName());
                if (resolver instanceof DocumentResolver) {
                    DocumentResolver documentResolver = (DocumentResolver) resolver;
                    newDT = documentResolver.resolve(newDT);
                } else if (resolver instanceof SentenceResolver) {
                    SentenceResolver sentenceResolver = (SentenceResolver) resolver;
                    final DocTheory.Builder docBuilder = newDT.modifiedCopyBuilder();

                    for (int i = 0; i < newDT.numSentences(); ++i) {
                        SentenceTheory st = newDT.sentenceTheory(i);
                        docBuilder.replacePrimarySentenceTheory(st, sentenceResolver.resolve(st));
                    }
                    newDT = docBuilder.build();
                } else if (resolver instanceof EventMentionResolver) {
                    EventMentionResolver eventMentionResolver = (EventMentionResolver) resolver;
                    final DocTheory.Builder docBuilder = newDT.modifiedCopyBuilder();

                    for (int i = 0; i < newDT.numSentences(); ++i) {
                        SentenceTheory st = newDT.sentenceTheory(i);
                        final EventMentions.Builder eventMentionsBuilder = new EventMentions.Builder();

                        for (EventMention em : st.eventMentions()) {
                            java.util.Optional<EventMention> newEM = eventMentionResolver.resolve(em);
                            if (newEM.isPresent()) {
                                eventMentionsBuilder.addEventMentions(newEM.get());
                            }
                        }
                        final SentenceTheory.Builder sentBuilder = st.modifiedCopyBuilder();
                        sentBuilder.eventMentions(eventMentionsBuilder.build());
                        docBuilder.replacePrimarySentenceTheory(st, sentBuilder.build());
                    }
                    newDT = docBuilder.build();
                }
            }
            return newDT;

    }

    public static byte[] getBytesFromDocTheory(DocTheory docTheory) throws IOException {
        SerifXMLWriter serifXMLWriter = SerifXMLWriter.create();
        StringWriter stringWriter = new StringWriter();
        serifXMLWriter.saveTo(docTheory,stringWriter);
        return stringWriter.toString().getBytes();
    }

    public static DocTheory getDocTheoryFromBytes(byte[] inBuffer) throws IOException {
        ByteArrayOutputStream result = new ByteArrayOutputStream();
        result.write(inBuffer);
        String xmlString = result.toString("UTF-8");
        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().allowSloppyOffsets().build();
        return serifXMLLoader.loadFromString(xmlString);
    }

    public static void main(String[] argv) throws Exception {
        final Parameters params = Parameters.loadSerifStyle(new File(argv[0]));
        // Input/output
        final File inputSerifxmlList = params.getExistingFile("input_serifxml_list");
        final File outputSerifxmlDirectory =
                params.getAndMakeDirectory("output_serifxml_directory");
        final SerifXMLLoader loader = SerifXMLLoader.builderWithDynamicTypes().allowSloppyOffsets().build();
        final SerifXMLWriter writer = SerifXMLWriter.create();
        DocTheoryResolver docTheoryResolver = new DocTheoryResolver(params);


        // Iterate over serifxmls, apply each resolver in order to each one and write
        for (final File inputFile : FileUtils.loadFileList(inputSerifxmlList)) {
            final DocTheory dt = loader.loadFrom(inputFile);
            DocTheory newDT = docTheoryResolver.resolve(dt);
            File outputSerifXMLFile = new File(outputSerifxmlDirectory, newDT.docid() + ".xml");
            writer.saveTo(newDT, outputSerifXMLFile);
        }
        System.out.println("Done applying resolvers");

    }

}

