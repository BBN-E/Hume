package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.nlp.corpora.ere.EREException;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;

import java.io.File;
import java.io.IOException;
import java.io.StringReader;
import java.util.Map;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import static com.bbn.bue.common.xml.XMLUtils.directChild;

/**
 * Created by ychan on 5/17/16.
 */
public final class ReadAnnotationXML {
  private static final Logger log = LoggerFactory.getLogger(ReadAnnotationXML.class);

  public static void main(String[] argv) {
    // we wrap the main method in this way to
    // ensure a non-zero return value on failure
    try {
      trueMain(argv);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(1);
    }
  }

  public static void trueMain(final String[] argv) throws IOException, ClassNotFoundException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    // a file listing the ENE XML annotation files
    final File xmlFileList = params.getExistingFile("ene.annotation.xmlFilelist");

    final ImmutableMultimap.Builder<String, String> idsBuilder = ImmutableMultimap.builder();
    for(final String xmlFile : Files.asCharSource(xmlFileList, Charsets.UTF_8).readLines()) {
      final AnnotationDocument document = loadFrom(new File(xmlFile));
      idsBuilder.putAll(getIdsToLabel(document));
    }
    final ImmutableMultimap<String, String> ids = idsBuilder.build();

    Files.asCharSink(params.getCreatableFile("ene.annotation.positive.ids"), Charsets.UTF_8).writeLines(ids.get(POSITIVE_LABEL).asList());
    Files.asCharSink(params.getCreatableFile("ene.annotation.negative.ids"), Charsets.UTF_8).writeLines(ids.get(NEGATIVE_LABEL).asList());
  }

  private static ImmutableMultimap<String, String> getIdsToLabel(final AnnotationDocument document) {
    final ImmutableMultimap.Builder<String, String> ret = ImmutableMultimap.builder();

    for(final Map.Entry<String, ImmutableSet<String>> entry : document.getGroupIds().entrySet()) {
      final String label = entry.getKey();
      if(label.compareTo(MISC)==0) {
        for(final String id : entry.getValue()) {
          ret.put(NEGATIVE_LABEL, id);
        }
      } else {
        for(final String id : entry.getValue()) {
          ret.put(POSITIVE_LABEL, id);
        }
      }
    }

    return ret.build();
  }

  public static AnnotationDocument loadFrom(final File f) throws IOException {
    try {
      return loadFrom(Files.toString(f, Charsets.UTF_8));
    } catch (IOException e) {
      throw e;
    } catch (Exception e) {
      throw new IOException(String.format("Error loading XML document %s", f.getAbsolutePath()), e);
    }
  }

  private static AnnotationDocument loadFrom(String s) throws IOException {

    final InputSource in = new InputSource(new StringReader(s.replaceAll("\r", "\n")));
    try {
      DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
      factory.setValidating(false);
      factory.setNamespaceAware(true);
      factory.setFeature("http://xml.org/sax/features/namespaces", false);
      factory.setFeature("http://xml.org/sax/features/validation", false);
      factory.setFeature("http://apache.org/xml/features/nonvalidating/load-dtd-grammar", false);
      factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
      DocumentBuilder builder = factory.newDocumentBuilder();
      return loadFrom(builder.parse(in));
    } catch (ParserConfigurationException e) {
      throw new EREException("Error parsing xml", e);
    } catch (SAXException e) {
      throw new EREException("Error parsing xml", e);
    }
  }

  private static AnnotationDocument loadFrom(org.w3c.dom.Document xml) {
    final AnnotationDocument.Builder documentBuilder = AnnotationDocument.builder();

    final Element root = xml.getDocumentElement();
    final String rootTag = root.getTagName();
    if (rootTag.equalsIgnoreCase("response")) {
      final Optional<Element> responseChild = directChild(root, "response");
      if (responseChild.isPresent()) {
        final Optional<Element> viewChild = directChild(responseChild.get(), "view");
        if(viewChild.isPresent()) {
          documentBuilder.withGroupIds(getGroupIds(viewChild.get()));
        }
      }
    }

    return documentBuilder.build();
  }

  private static ImmutableMap<String, ImmutableSet<String>> getGroupIds(final Element viewElement) {
    final ImmutableMap.Builder<String, ImmutableSet<String>> ret = ImmutableMap.builder();

    for (Node child = viewElement.getFirstChild(); child != null; child = child.getNextSibling()) {
      if (child instanceof Element) {
        final Element groupElement = (Element) child;
        assert(groupElement.getTagName().equals("group"));

        final String groupLabel = groupElement.getAttribute("label");

        final ImmutableSet<String> groupIds = getIds(groupElement);

        ret.put(groupLabel, groupIds);
      }
    }

    return ret.build();
  }


  private static ImmutableSet<String> getIds(final Element groupElement) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    for(Node child = groupElement.getFirstChild(); child!=null; child=child.getNextSibling()) {
      if(child instanceof Element) {
        final Element element = (Element)child;
        if(element.getTagName().equals("cite")) {
          ret.add(element.getAttribute("number"));
        }
      }
    }

    return ret.build();
  }

  public static final class AnnotationDocument {
    final ImmutableMap<String, ImmutableSet<String>> groupIds;

    private AnnotationDocument(final ImmutableMap<String, ImmutableSet<String>> groupIds) {
      this.groupIds = groupIds;
    }

    public ImmutableMap<String, ImmutableSet<String>> getGroupIds() {
      return groupIds;
    }

    public String printGroupIds() {
      final StringBuilder sb = new StringBuilder();

      for(final Map.Entry<String, ImmutableSet<String>> entry : groupIds.entrySet()) {
        final String label = entry.getKey();
        for(final String id : entry.getValue()) {
          sb.append(label + "\t" + id + "\n");
        }
      }

      return sb.toString();
    }

    public static Builder builder() {
      return new Builder();
    }

    public static class Builder {
      final ImmutableMap.Builder<String, ImmutableSet<String>> groupIdsBuilder;

      private Builder() {
        groupIdsBuilder = ImmutableMap.builder();
      }

      public Builder withGroupIds(final ImmutableMap<String, ImmutableSet<String>> groupIds) {
        this.groupIdsBuilder.putAll(groupIds);
        return this;
      }

      public AnnotationDocument build() {
        return new AnnotationDocument(groupIdsBuilder.build());
      }
    }
  }

  private final static String MISC = new String("MISCELLANEOUS");
  private final static String POSITIVE_LABEL = new String("1");
  private final static String NEGATIVE_LABEL = new String("0");
}
