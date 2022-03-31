This section describes how to deploy the Hume Ontology In A Day (OIAD) clustering service.

## System Preparation

To deploy the Hume OIAD clustering service, you will need to prepare a json config file. 

You will also need to create a new working folder, we'll use `oiad_runtime` as an example in this document.

### Docker Config File

The config file is a json file that must be visible at runtime from `/extra/config.json` inside the container. An example is provided as follows:

```json
{
  "CDR_retrieval": "str,required: for example https://wm-ingest-pipeline-rest-1.prod.dart.worldmodelers.com/dart/api/v1/cdrs",
  "auth": {
    "username": "str,required",
    "password": "str,required"
  },
  "hume.oiad.use_local_cdrs": "bool, optional: when enable, we'll use locally available cdrs instead of fetching CDRs from DART. When enable, please set hume.cdr_cache_dir as well",
  "hume.anaconda_root": "/usr/local/",
  "hume.use_regrounding_cache": "bool, optional: When enabled, the system will save intermediate files of processing result into a directory that if we see the same document later, we can skip certain processing steps and only kick off regrounding pipeline.",
  "hume.regrounding_cache_path": "str, required when hume.use_regrounding_cache is true: a persist directory for hosting regrounding cache. Ideally to be a persist storage that can be shared in between docker instances. Also please don't reuse grounding cache from BYOD.",
  "hume.oiad.port": "int, required: port number to listen. You need to expose the port to outside docker by -p . In the example we assume the port is 5050",
  "hume.oiad.runtime_dir": "str, required: A directory inside docker for tmp purpose. All files under this directory may be deleted.",
  "hume.cdr_cache_dir": "str or null, optional, required when hume.oiad.use_local_cdrs is true: When specified, Hume will use the path from inside docker to cache CDRs locally so when new reading requests come as long as it's found in local cache, it won't goto API for fetching it again.  Each of those needs to be named as \"[document_id].json\" without []"
}
```

Please copy the config file to `oiad_runtime/config.json`

## To Run Hume OIAD Clustering Service

```bash
docker run --rm -it -v $PWD/oiad_runtime:/extra -p 5050:5050 docker.io/wmbbn/hume:R2022_03_21 /usr/local/envs/hat_new/bin/python3 /wm_rootfs/git/Hume/src/python/concept_discovery_dart_integration/concept_discovery_online/api.py --config /extra/config.json
```
