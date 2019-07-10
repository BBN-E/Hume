package com.bbn.necd.common.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.CollectionUtils;
import com.bbn.necd.common.RealInstanceManager;
import com.bbn.necd.common.metric.MemberSimilarity;
import com.bbn.necd.common.metric.SimilarityMetric.MetricType;
import com.bbn.necd.common.sampler.SymbolPair;

import com.google.common.base.Charsets;
import com.google.common.base.Function;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Ordering;
import com.google.common.collect.Table;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Map;

/*
  Parameters:
  - metricType
  - memberPair.label (optional)
*/
public final class GenerateMemberSimilarity {
  private static final Logger log = LoggerFactory.getLogger(GenerateMemberSimilarity.class);

  private final ImmutableTable<Symbol, Symbol, Double> memberSimilarity;
  private final Optional<File> labelFile;

  private GenerateMemberSimilarity(final ImmutableTable<Symbol, Symbol, Double> memberSimilarity, final Optional<File> labelFile) {
    this.memberSimilarity = memberSimilarity;
    this.labelFile = labelFile;
  }

  public static GenerateMemberSimilarity from(final Parameters params, final RealInstanceManager realInstanceManager) {
    final MetricType metricType = params.getEnum("metricType", MetricType.class);

    final ImmutableTable<Symbol, Symbol, Double> memberSimilarity = MemberSimilarity.calculateInterSimilarity(
        realInstanceManager, metricType);

    final Optional<File> labelFile = params.getOptionalExistingFile("memberPair.label");

    return new GenerateMemberSimilarity(memberSimilarity, labelFile);
  }

  public ImmutableTable<Symbol, Symbol, Double> getMemberSimilarity() {
    return memberSimilarity;
  }

  public void calculateSimilarityToFile(final File outfile) throws IOException {
    sortSimilarityTableToFile(memberSimilarity, outfile);

    if(labelFile.isPresent()) {
      final ImmutableMap<SymbolPair, Symbol> pairLabels = TrainSimilarityMetric.readPairLabel(labelFile.get());

      int tp = 0;     // true positive
      int tn = 0;     // true negative
      int N = 0;      // total number of examples

      for(final Table.Cell<Symbol, Symbol, Double> cell : memberSimilarity.cellSet()) {
        final SymbolPair idPair = SymbolPair.from(cell.getRowKey(), cell.getColumnKey());
        if(pairLabels.containsKey(idPair)) {
          final int y = Integer.valueOf(pairLabels.get(idPair).asString());
          final double hx = cell.getValue();

          if(y==0 && hx<0.5) {
            tn += 1;
          } else if(y==1 && hx>=0.5) {
            tp += 1;
          }

          N += 1;
        }
      }

      log.info("TP={}, TN={}, N={}, accuracy={}", tp, tn, N, ((double)(tp+tn))/N );
    }
  }

  /*
  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final RealInstanceManager realInstanceManager = RealInstanceManager.from(params);

    final MetricType metricType = params.getEnum("metricType", MetricType.class);

    final ImmutableTable<Symbol, Symbol, Double> memberSimilarity = MemberSimilarity.calculateInterSimilarity(
        realInstanceManager, metricType);

    System.out.println("Sorting similarity to file");
    sortSimilarityTableToFile(memberSimilarity, params.getCreatableFile("interMemberSimilarity"));

    if(params.isPresent("memberPair.label")) {
      final ImmutableMap<SymbolPair, Symbol> pairLabels =
          TrainSimilarityMetric.readPairLabel(params.getExistingFile("memberPair.label"));

      int tp = 0;     // true positive
      int tn = 0;     // true negative
      int N = 0;      // total number of examples

      for(final Table.Cell<Symbol, Symbol, Double> cell : memberSimilarity.cellSet()) {
        final SymbolPair idPair = SymbolPair.from(cell.getRowKey(), cell.getColumnKey());
        if(pairLabels.containsKey(idPair)) {
          final int y = Integer.valueOf(pairLabels.get(idPair).asString());
          final double hx = cell.getValue();

          if(y==0 && hx<0.5) {
            tn += 1;
          } else if(y==1 && hx>=0.5) {
            tp += 1;
          }

          N += 1;
        }
      }

      log.info("TP={}, TN={}, N={}, accuracy={}", tp, tn, N, ((double)(tp+tn))/N );
    }
  }
  */

  private static void sortSimilarityTableToFile(final ImmutableTable<Symbol, Symbol, Double> table, final File outfile) throws IOException {
    final ImmutableList.Builder<String> lines = ImmutableList.builder();

    final ImmutableList<Symbol> sortedItems = Ordering.natural().onResultOf(SYMBOL_STRING).immutableSortedCopy(table.rowKeySet());
    for(final Symbol item : sortedItems) {
      for(final Map.Entry<Symbol, Double> entry : CollectionUtils.entryValueOrdering.sortedCopy(table.row(item).entrySet())) {
        lines.add(item.asString() + " " + entry.getKey().asString() + " " + entry.getValue());
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines.build());
  }

  private static final Function<Symbol, String> SYMBOL_STRING =
      new Function<Symbol, String>() {
        @Override
        public String apply(final Symbol input) {
          return input.asString();
        }
      };

}

