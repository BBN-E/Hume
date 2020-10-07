# Hume
BBN's machine reading system with support from
 DARPA [World Modelers](https://www.darpa.mil/program/world-modelers)
and [Causal Exploration](https://www.darpa.mil/program/causal-exploration) programs. 

For this release, we're providing both streaming implementation and batching implementation that will seamlessly integrate with TwoSix's Kafka pipeline. For batching implementation, as we don't have a good way to know that we have received all messages, we use a parameter to set a timeout. We consider streaming implementation as a special case of batching implementation in the sense that 1) Batch size is very small (e.g., could be `1`), 2) We'll keep listening to Kafka messages. 

### System requirement

To run Hume, you need a machine with at least 2 cores, 16GB RAM. Also we're assuming it's a Linux machine with [Docker](https://www.docker.com/) installed. 

### Data preparation

Please download this file to your local machine (Please email [Haoling](mailto:haoling.qiu@raytheon.com) if you want access). Download the tgz files and unzip:

1. `cx-dependency.tar.gz`
2. `2a03df7162a6.tar.gz`


### Load docker image

```bash
docker load --input 2a03df7162a6.tar.gz
```

### Test BBN TA1 CauseEx pipeline

We're also providing an example config file. It's extended from https://github.com/twosixlabs-dart/python-kafka-consumer/blob/master/pyconsumer/resources/env/test.json and includes extra parameters that Hume require.

```
CDR_retrieval: # URI for receiving cdr.
DART_upload: # URI for submitting rdf triples back
hume.domain: "CAUSEEX" # Don't change this.
hume.num_of_vcpus # Number of cpu cores available to you. It at least needs to be 2, and please only include number of physical cores instead of SMT cores.
hume.tmp_dir: # Don't change this.
hume.batching.kafka_timeout: # When using batching mode, how many seconds should Hume listen to kafka message queue. After the time out, the system will assume that all messages have been received and will start processing.
hume.batching.maximum_num_of_cdrs_for_processing: # This is a debugging switch for batching mode. If null, all kafka messages will be processed. If an int specified, Hume will process at most that number of messages.
hume.streaming.mini_batch_size: # For streaming mode, this deterimines the size of a mini batch (which is used for improved efficiency)
hume.streaming.mini_batch_wait_time: # For streaming mode, even if we received fewer documents than mini_batch_size, the system will start processing after mini_batch_wait_time seconds.
hume.laptop_mode: false # If set to be true, the system will limit memory usage and run some components in a simplified setting to improve efficiency when running on a laptop.
```

After you finished the change, please name it as `config.json` and put it under `$PWD/runtime`.

Then you can run the system in the batch, streaming, or laptop mode:

For batch mode, 

```
docker run --rm --net=host --mount type=bind,source=$PWD/runtime,target=/extra --mount type=bind,source=$PWD/causeex_dependency,target=/dependencies --name hume_batch_mode 2a03df7162a6 /usr/local/envs/py3-jni/bin/python3 /wm_rootfs/git/Hume/src/python/dart_integration/batching_processing.py
```

For streaming mode,

```
docker run --rm --net=host --mount type=bind,source=$PWD/runtime,target=/extra --mount type=bind,source=$PWD/causeex_dependency,target=/dependencies --name hume_stream_mode 2a03df7162a6 /usr/local/envs/py3-jni/bin/python3 /wm_rootfs/git/Hume/src/python/dart_integration/streaming_processing.py
```

For running on a laptop, please run the above command for either "batch mode" or "streaming mode" with hume.laptop_mode set to be true. 

