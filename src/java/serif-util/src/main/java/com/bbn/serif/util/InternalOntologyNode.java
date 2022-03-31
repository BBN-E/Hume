package com.bbn.serif.util;

import com.google.common.base.Optional;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Created by ychan on 4/17/19.
 */
public class InternalOntologyNode {

    public List<InternalOntologyNode> children;
    public String originalKey;
    public Optional<InternalOntologyNode> parent;

    public List<String> _source;
    public String _description;
    public List<String> _examples;
    public String _alternative_id;
    public List<String> _is_a;

    public InternalOntologyNode() {
        this.children = new ArrayList<>();
        this.parent = Optional.absent();
        this._source = new ArrayList<>();
        this._examples = new ArrayList<>();
        this.parent = Optional.absent();
        this._alternative_id = null;
        this._is_a = new ArrayList<>();
    }

    public static InternalOntologyNode buildInternalOntologyHierachy(List<Map> root,
        String originalKey) {

        InternalOntologyNode newOntologyRoot = new InternalOntologyNode();
        newOntologyRoot.originalKey = originalKey;

        for (Map i : root) {
            for (Object dictKeyObj : i.keySet()) {
                String key = (String) dictKeyObj;
                if (key.startsWith("_")) {
                    if (key.equals("_source")) {
                        for (Object sourceObj : (List<Object>) i.get(dictKeyObj)) {
                            String sourceVal = (String) sourceObj;
                            newOntologyRoot._source.add(sourceVal);
                        }
                    } else if (key.equals("_description")) {
                        newOntologyRoot._description = (String) i.get(dictKeyObj);
                    } else if (key.equals("_examples")) {
                        for (Object exampleObj : (List<Object>) i.get(dictKeyObj)) {
                            String exampleVal = (String) exampleObj;
                            newOntologyRoot._examples.add(exampleVal);
                        }
                    } else if (key.equals("_alternative_id")) {
                        newOntologyRoot._alternative_id = (String) i.get(dictKeyObj);
                    }
                    else if (key.equals("_is_a")) {
                        for (String _is_a : (List<String>) i.get(dictKeyObj)) {
                            if (!_is_a.toLowerCase().equals("na")) {
                                newOntologyRoot._is_a.add(_is_a);
                            }
                        }
                    }
                    else {
                        throw new RuntimeException("The field " + key
                            + " is reserved for internal usage, which you didn't parse it");
                    }
                } else {
                    newOntologyRoot.children
                        .add(buildInternalOntologyHierachy((List<Map>) i.get(dictKeyObj), key));
                }
            }
        }

        for (InternalOntologyNode child : newOntologyRoot.children) {
            child.parent = Optional.of(newOntologyRoot);
        }

        return newOntologyRoot;
    }
}
