package com.bbn.serif.util;

import com.google.common.collect.Multimap;

import java.util.Stack;
import java.util.stream.Collectors;

public class InternalOntology {

    public static void DFSDotIdBasedPathParsing(InternalOntologyNode root, Stack<InternalOntologyNode> currentStack, Multimap<String,String> leafToFullPath){
        currentStack.push(root);
        leafToFullPath.put(root.originalKey,currentStack.stream().map(i->i.originalKey).collect(Collectors.joining(".")));
        /*
        if(!leafToFullPath.containsKey(root.originalKey)){
            leafToFullPath.put(root.originalKey,currentStack.stream().map(i->i.originalKey).collect(Collectors.joining(".")));
        }
        else{
            throw new RuntimeException("InternalOntologyNode id duplicates detected, id: "+root.originalKey);

            // @hqiu: Below is @ychan's original intention for resolving duplication

//            final int currentPathLength = leafToFullPath.get(root._id).split(Pattern.quote(".")).length;
//            final int newPathLength = currentStack.size();
//            if(newPathLength < currentPathLength) {
//                leafToFullPath.put(root._id, currentStack.stream().map(i->i._id).collect(Collectors.joining(".")));
//            }
        }
        */
        for(InternalOntologyNode child:root.children){
            DFSDotIdBasedPathParsing(child,currentStack,leafToFullPath);
        }
        currentStack.pop();
    }

    public static void DFSNodeNameToSlashJointNodePathMapParsing(InternalOntologyNode root,Stack<InternalOntologyNode> currentStack,Multimap<String,String> NodeNameToSlashJointMap){
        currentStack.push(root);
        NodeNameToSlashJointMap.put(root.originalKey,"/" + currentStack.stream().map(i->i.originalKey).collect(Collectors.joining("/")));
        for(InternalOntologyNode child:root.children){
            DFSNodeNameToSlashJointNodePathMapParsing(child,currentStack,NodeNameToSlashJointMap);
        }
        currentStack.pop();
    }
}
