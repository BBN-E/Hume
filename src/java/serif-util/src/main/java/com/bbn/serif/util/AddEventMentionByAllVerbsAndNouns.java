package com.bbn.serif.util;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.io.SerifXMLWriter;
import com.bbn.serif.theories.*;
import com.google.common.collect.ImmutableList;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class AddEventMentionByAllVerbsAndNouns {

    public static List<String> readLinesIntoList(String file) throws IOException {
        List<String> lines = new ArrayList<>();
        int nLine = 0;
        BufferedReader reader;
        String sline;
        for (reader = new BufferedReader(new FileReader(file)); (sline = reader.readLine()) != null; lines.add(sline)) {
            if (nLine++ % 100000 == 0) {
                System.out.println("# lines read: " + nLine);
            }
        }
        reader.close();
        return lines;
    }

    static class MySynNodeVisiter implements SynNode.PreorderVisitor{
        final Set<SynNode> coveredSynNode;
        MySynNodeVisiter(){
            coveredSynNode = new HashSet<>();
        }
        @Override
        public boolean visitChildren(SynNode synNode) {
            if(!coveredSynNode.contains(synNode)){
                coveredSynNode.add(synNode);
                return true;
            }
            else return false;
        }
    }

    public static DocTheory addEventMentions(DocTheory input){
        final DocTheory.Builder docBuilder = input.modifiedCopyBuilder();
        for (int i = 0; i < input.numSentences(); ++i) {
            final SentenceTheory st = input.sentenceTheory(i);

            final SentenceTheory.Builder sentBuilder = st.modifiedCopyBuilder();
            final ImmutableList.Builder<EventMention> newEventMentions =
                    ImmutableList.builder();
            Set<SynNode> existingEventSynNode = new HashSet<>();

            for (EventMention eventMention : st.eventMentions()) {
                newEventMentions.add(eventMention);
                if(eventMention.anchorNode() != null)existingEventSynNode.add(eventMention.anchorNode());
                for(EventMention.Anchor anchor : eventMention.anchors()){
                    if(anchor.anchorNode()!=null)existingEventSynNode.add(anchor.anchorNode());
                }
            }
            MySynNodeVisiter mySynNodeVisiter = new MySynNodeVisiter();
            if (!st.parse().root().isPresent()) continue;;
            SynNode parseRoot = st.parse().root().get();
//            for(Mention mention: st.mentions()){
//                mention.node().preorderTraversal(mySynNodeVisiter);
//            }
            for(int j = 0;j < parseRoot.numTerminals(); j++){
                final SynNode node = parseRoot.nthTerminal(j);
                final String posTag = node.headPOS().asString();
                if(posTag.startsWith("VB") || posTag.matches("NNS?")){
                    if(!mySynNodeVisiter.coveredSynNode.contains(node) && !existingEventSynNode.contains(node)){
                        EventMention em = EventMention
                                .builder(Symbol.from("Event"))
                                .setAnchorNode(node)
                                .setScore(0.3)
                                .build();
                        existingEventSynNode.add(node);
                        newEventMentions.add(em);
                    }
                }
            }

            sentBuilder.eventMentions(new EventMentions.Builder()
                    .eventMentions(newEventMentions.build())
                    .build());
            docBuilder.replacePrimarySentenceTheory(st, sentBuilder.build());
        }
        return docBuilder.build();
    }

    public static void main(String[] args) throws Exception{
        String strListSerifXmlFiles = args[0];
        String strOutputDir = args[1];

        List<String> listStringFiles = readLinesIntoList(strListSerifXmlFiles);

        List<File> filesToProcess = new ArrayList<>();

        for (String strFile : listStringFiles) {
            System.out.println("Reading " + strFile);
            filesToProcess.add(new File(strFile));
        }

        SerifXMLWriter serifXMLWriter = SerifXMLWriter.create();
        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().allowSloppyOffsets().build();

        for (final DocTheory dt : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
            DocTheory docTheoryWithNewEvents = addEventMentions(dt);
            String strOutputSerifXml = strOutputDir + "/" + dt.docid().asString() + ".xml";
            serifXMLWriter.saveTo(docTheoryWithNewEvents, strOutputSerifXml);
        }
    }
}
