package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.theories.ValueMention;
import com.bbn.serif.theories.ValueMentions;
import com.bbn.serif.types.ValueType;
import com.bbn.serif.util.resolver.Resolver;
import com.google.common.collect.Sets;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public class PropertyAsValueMentionResolver implements SentenceResolver, Resolver {
    @Override
    public SentenceTheory resolve(SentenceTheory sentenceTheory) {

        Set<String> priceWords = Sets.newHashSet("price","prices","cost","costs");
        List<ValueMention> valueMentions = new ArrayList<>(sentenceTheory.valueMentions().asList());
        for(SynNode synNode:sentenceTheory.parse().preterminalNodes()){
            String token = synNode.firstTerminal().span().tokenizedText().utf16CodeUnits().toLowerCase();
            String posTag = synNode.firstTerminal().headPOS().asString();
            if(!posTag.startsWith("VB") && priceWords.contains(token)){
                ValueMention valueMention = ValueMention.builder(ValueType.parseDottedPair("PRICE"),synNode.span()).build();
                valueMentions.add(valueMention);
            }
        }
        SentenceTheory modifiedSentenceTheory = sentenceTheory.modifiedCopyBuilder().valueMentions(ValueMentions.create(valueMentions)).build();
        return modifiedSentenceTheory;
    }
}
