package com.bbn.serif.util;

import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.*;
import com.google.common.base.Joiner;
import com.google.common.collect.Lists;

import java.io.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class NeuralNamesModelInputOutputMapper {

    // Example output: 0       2       Hirabai Badodekar , Gangubai Hangal , Mogubai Kurdikar -RRB- , made the Indian classical music so much greater .        /person/artist /person  HEAD|Badodekar NON_HEAD|Hirabai PARENT|made CLUSTER| CHARACTERS|:ba CHARACTERS|bad CHARACTERS|ado CHARACTERS|dod CHARACTERS|ode CHARACTERS|dek CHARACTERS|eka CHARACTERS|kar CHARACTERS|ar: SHAPE|AasAa ROLE|nsubj BEFORE|<s> AFTER|,

    private static String generateLineFromNamedMention(Name name, SentenceTheory sentenceTheory) {
        StringBuilder stringBuilder = new StringBuilder();

        int nameStart = name.tokenSpan().startTokenIndexInclusive();
        int nameEnd = name.tokenSpan().endTokenIndexInclusive()+1;

        stringBuilder.append(nameStart + "\t");
        stringBuilder.append(nameEnd + "\t");

        stringBuilder.append(getTokenSequence(sentenceTheory) + "\t");

        stringBuilder.append(name.type().name().asString() + "\t");
        stringBuilder.append(getFeatures(name, sentenceTheory));

        return stringBuilder.toString().trim();
    }

    // TODO: fix this with head node in parse
    private static int getHeadIdx(Name name, SentenceTheory sentenceTheory) {
        return name.tokenSpan().endTokenIndexInclusive();
    }

    private static String getFeatures(Name name, SentenceTheory sentenceTheory) {
        StringBuilder stringBuilder = new StringBuilder();

        int headIdx = getHeadIdx(name, sentenceTheory);
        for(int tid=name.tokenSpan().startTokenIndexInclusive(); tid<=name.tokenSpan().endTokenIndexInclusive(); tid++) {
            String tokenText = sentenceTheory.tokenSequence().token(tid).tokenizedText().utf16CodeUnits()
                    .replace("\n", "").replace("\t", "");
            if(headIdx==tid)
                stringBuilder.append("HEAD|" + tokenText + " ");
            else
                stringBuilder.append("NON_HEAD|" + tokenText + " ");
        }

        return stringBuilder.toString().trim();
    }

    private static String getTokenSequence(SentenceTheory sentenceTheory) {
        StringBuilder stringBuilder = new StringBuilder();

        for(int tid=0; tid<sentenceTheory.tokenSequence().size(); tid++) {
            Token token = sentenceTheory.tokenSequence().token(tid);
            stringBuilder.append(token.tokenizedText().utf16CodeUnits() + " ");
        }

        return stringBuilder.toString().trim();
    }

    public static void main(String [] argv) throws IOException {
        try{
            trueMain(argv);
        }catch (Exception e){
            e.printStackTrace();
            System.exit(1);
        }
    }
    private static void trueMain(String [] argv) throws IOException {
        String strListSerifXmlFiles = argv[0];
        String nnTypingInputFile = argv[1];
        String nameObjectReconstructionInfoFile = argv[2];

        BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(strListSerifXmlFiles)));
        PrintWriter printWriterNNTyping = new PrintWriter(new File(nnTypingInputFile));
        PrintWriter printWriterReconstruction = new PrintWriter(new File(nameObjectReconstructionInfoFile));

        Map<String,File> filesToProcess = new HashMap();
        String line = null;
        while((line = br.readLine())!=null){
            filesToProcess.put(line,new File(line));
        }
        br.close();

        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().build();
        for (String serifXmlPath : filesToProcess.keySet()) {
            DocTheory dt = serifXMLLoader.loadFrom(filesToProcess.get(serifXmlPath));
            for (int sid=0; sid<dt.numSentences(); sid++) {
                SentenceTheory sentenceTheory = dt.sentenceTheory(sid);
                for(Name name : sentenceTheory.names()) {
                    String linesForInstance = generateLineFromNamedMention(name, sentenceTheory);
                    printWriterNNTyping.println(linesForInstance);
                    printWriterReconstruction.println(getInstanceStringForName(name,sid,serifXmlPath));
                }
            }
        }
        printWriterNNTyping.close();
        printWriterReconstruction.close();

    }

    public static String getInstanceStringForName(Name name, int sentenceId, String serifXmlPath){
        return Joiner.on("\t").join(
                Lists.newArrayList(serifXmlPath,sentenceId,name.tokenSpan().startTokenIndexInclusive(),
                        name.span().endTokenIndexInclusive()+1,name.type().name().asString()));
    }
}
