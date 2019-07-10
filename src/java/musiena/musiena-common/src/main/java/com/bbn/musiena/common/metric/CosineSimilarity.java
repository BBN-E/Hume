package com.bbn.musiena.common.metric;

import com.bbn.musiena.common.CollectionUtils;
import com.bbn.musiena.common.theory.RealVector;

import com.google.common.base.Charsets;
import com.google.common.collect.HashBasedTable;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import com.google.common.collect.Table;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static com.google.common.base.Preconditions.checkArgument;

public final class CosineSimilarity {
  private static final Logger log = LoggerFactory.getLogger(CosineSimilarity.class);

  private final ImmutableList<RealVector> vectors;
  private final ImmutableList<Double> norms;
  private final int numberOfThreads;
  private final String outputDir;
  private final int topK;
  private final double simThreshold;

  private CosineSimilarity(final ImmutableList<RealVector> vectors, final ImmutableList<Double> norms, final int numberOfThreads, final String outputDir, final int topK, final double simThreshold) {
    this.vectors = ImmutableList.copyOf(vectors);
    this.norms = ImmutableList.copyOf(norms);
    checkArgument(numberOfThreads >= 1);
    this.numberOfThreads = numberOfThreads;
    this.outputDir = outputDir;
    this.topK = topK;
    this.simThreshold = simThreshold;
  }

  public static CosineSimilarity from(final ImmutableList<RealVector> vectors, final int numberOfThreads, final String outputDir, final int topK, final double simThreshold) {
    final ImmutableList<Double> norms = calculateL2Norms(vectors);
    return new CosineSimilarity(vectors, norms, numberOfThreads, outputDir, topK, simThreshold);
  }


  public void doTraining() throws IOException {
    log.info("Start training");

    ExecutorService threadPool = Executors.newFixedThreadPool(numberOfThreads);

    try {
      BlockingQueue<SubCorpus> corpusQueue =
          new ArrayBlockingQueue<SubCorpus>(numberOfThreads);
      List<Future> futures = Lists.newArrayList();

      for (int i = 0; i < numberOfThreads; i++) {
        futures.add(threadPool.submit(new Trainer(corpusQueue)));
      }

      // we now create lists of indices to pass to the individual threads
      List<Integer> indices = Lists.newArrayList();
      final int corpusSize = Double.valueOf(Math.ceil((double)vectors.size()/numberOfThreads)).intValue();
      int runningIndex = 0;
      while(runningIndex < vectors.size()) {
        indices.add(runningIndex);
        runningIndex += 1;
        if(indices.size() >= corpusSize) {
          corpusQueue.put(SubCorpus.from(indices));
          indices.clear();
        }
      }

      if(indices.size() > 0) {
        corpusQueue.put(SubCorpus.from(indices));
        indices.clear();
      }

      for (Future future : futures) {
        future.get();
      }
      threadPool.shutdown();
    } catch (InterruptedException e) {
      e.printStackTrace();
    } catch (ExecutionException e) {
      e.printStackTrace();
    }
  }


  public static double similarity(final RealVector v1, final RealVector v2) {
    return similarity(v1.vector(), calculateL2Norm(v1.vector()), v2.vector(), calculateL2Norm(v2.vector()));
  }

    public static double similarity(final double[] v1, final double v1Norm, final double[] v2, final double v2Norm) {
    return dotProduct(v1, v2)/(v1Norm*v2Norm);
  }

  public static double similarity(final double[] v1, final double[] v2) {
    return dotProduct(v1, v2)/(calculateL2Norm(v1)*calculateL2Norm(v2));
  }

  public static double dotProduct(final double[] v1, final double[] v2) {
    checkArgument(v1.length == v2.length);

    double ret = 0;
    for(int i=0; i<v1.length; i++) {
      ret += v1[i] * v2[i];
    }

    return ret;
  }

  public static ImmutableList<Double> calculateL2Norms(final ImmutableList<RealVector> vectors) {
    final ImmutableList.Builder<Double> ret = ImmutableList.builder();

    for(final RealVector v : vectors) {
      final double norm = calculateL2Norm(v.vector());
      ret.add(norm);
    }

    return ret.build();
  }

  public static double calculateL2Norm(final double[] vector) {
    double f = 0;
    for(int i=0; i<vector.length; i++) {
      f += (vector[i] * vector[i]);
    }
    return Math.sqrt(f);
  }

  public void writeToFile(final Table<String, String, Double> table, final File outfile) throws IOException {

    final Writer writer = Files.asCharSink(outfile, Charsets.UTF_8).openBufferedStream();

    for(final String row : table.rowKeySet()) {
      final Map<String, Double> column = table.row(row);

      int k = 0;
      for (final Map.Entry<String, Double> entry : CollectionUtils.entryValueOrdering
          .immutableSortedCopy(column.entrySet())) {
        writer.write(row + " " + entry.getKey() + " " + entry.getValue() + "\n");

        k += 1;
        if(k >= topK) {
          break;
        }
      }
    }

    writer.close();
  }

  public final class Trainer implements Runnable {
    private BlockingQueue<SubCorpus> corpusQueue;

    public Trainer(BlockingQueue<SubCorpus> corpusQueue) {
      this.corpusQueue = corpusQueue;
    }

    private void training(final SubCorpus corpus) {
      final ImmutableList<Integer> items = corpus.getItems();

      int setIndex = 1;
      Table<String, String, Double> simTable = HashBasedTable.create();

      int counter = 0;
      for(final Integer item : items) {
        final double[] v1 = vectors.get(item).vector();
        final double v1Norm = norms.get(item);

        for(int j=0; j<vectors.size(); j++) {
          if(item.intValue() != j) {
            final double sim = similarity(v1, v1Norm, vectors.get(j).vector(), norms.get(j));
            if(sim >= simThreshold) {
              simTable.put(vectors.get(item).id(), vectors.get(j).id(), sim);
            }
          }
        }

        counter += 1;
        if((counter % 500)==0) {
          final long threadId = (Thread.currentThread().getId() % numberOfThreads) + 1;
          log.info("Thread {}, calculated {} out of {}", threadId, counter, items.size());

          try {
            writeToFile(simTable, new File(outputDir+"/"+threadId+"."+setIndex+".sim"));
          } catch (IOException e) {
            e.printStackTrace();
          }

          simTable.clear();
          setIndex += 1;
        }
      }

      // write out residue similarities
      if(simTable.size() > 0) {
        final long threadId = (Thread.currentThread().getId() % numberOfThreads) + 1;
        log.info("Thread {}, calculated {} out of {}", threadId, counter, items.size());

        try {
          writeToFile(simTable, new File(outputDir+"/"+threadId+"."+setIndex+".sim"));
        } catch (IOException e) {
          e.printStackTrace();
        }

        simTable.clear();
        setIndex += 1;
      }
    }

    @Override
    public void run() {
      boolean hasCorpus = true;

      try {
        while(hasCorpus) {
          final SubCorpus corpus = corpusQueue.poll(2, TimeUnit.SECONDS);
          if(corpus != null) {
            training(corpus);
          } else {
            hasCorpus = false;
          }
        }
      } catch(InterruptedException e) {
        e.printStackTrace();
      }
    }
  }

  public static final class SubCorpus {
    final ImmutableList<Integer> items;

    private SubCorpus(final ImmutableList<Integer> items) {
      this.items = ImmutableList.copyOf(items);
    }

    public static SubCorpus from(final List<Integer> items) {
      return new SubCorpus(ImmutableList.<Integer>builder().addAll(items).build());
    }

    public ImmutableList<Integer> getItems() {
      return items;
    }


  }

  //private final static int topK = 200;
  //private final static double simThreshold = 0.3;
}
