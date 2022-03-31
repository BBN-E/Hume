
All API calls described below are intended to run on the client side. In other words, a separate client process must communicate requests to the OIAD HTTP service running in Docker.

## Offline Processing (Corpus Seeding, Initial Clustering)

Before the clustering service can return meaningful cluster suggestions, a domain-relevant corpus must be provided to seed the clustering algorithm. The seeding process can be time-consuming; in our experiments it took `4.83` hours on a machine with 8 cores, using 16 threads to complete the seeding process for `256` analytical articles.

### Seed Job Submission

To submit a new corpus for seeding, send an HTTP POST request to `api/v1/concept_discovery/offline_processing/submit` with json content in the request body. An example curl call is:

```bash
curl --request POST \
  --url http://HTTPENDPOINT/api/v1/concept_discovery/offline_processing/submit \
  --header 'Content-Type: application/json' \
  --data @./offline_processing_5doc.json
```

The content of `offline_processing_5doc.json` should contain:

```json
{
    "relevant_doc_uuids":[  strings of doc uuids ],
    "allowed_words":[ strings of words from saliency list ],
    "ontology_metadata": "string of ontology_metadata file"
}
```

And will return:

```json
{
  "job_id": "0c70a96f-b34b-40ab-b588-7a38f7d4b8f3",
  "message": "Job submitted",
  "success": true
}
```

Note: `job_id` will vary. The `job_id` is hard-coded above to demonstrate the querying process (below).

### Polling Seed Job Status

To poll for clustering job status, send an HTTP GET request to `/api/v1/concept_discovery/offline_processing/job` with query `job_id=0c70a96f-b34b-40ab-b588-7a38f7d4b8f3`

```bash
curl --request GET \
  --url 'http://HTTPENDPOINT/api/v1/concept_discovery/offline_processing/job?job_id=0c70a96f-b34b-40ab-b588-7a38f7d4b8f3'
```

Depending on the status of the seeding process, there are several potential responses:

#### The job is still running

```json
{"success":true, "message":"Your session is not ready yet.","job_id":"job_id string","is_finished":false,"without_error":false,"job_log":"some debugging string for you to trace the progress"}
```

In short, `is_finished: False` means the job is running on the backend. The result is not yet ready.

The `job_log` field contains the stdout+stderr output from the backend side for developer usage. It will be refreshed as you call the endpoint, and can be used to help estimate the remaining time of the job. The corpus seeding process calls multiple batch sequences on the backend and execution time will vary between steps. 

#### The job is no longer running

There are three possibilities here
1. The job exited without error
2. The job exited with error
3. The job was killed (for example, if the docker container unexpectedly exited), or you provided an invalid job_id

##### The job exited without error

You'll see

```json
{"success":true, "message":"Your session is ready.","job_id":job_id,"is_finished":true,"without_error":true,"job_log":"some debugging string for you to trace the progress"}
```

The `is_finished: True`, `without_error: True` setting combination indicates success. At this point, you can start making online clustering service requests.

##### The job exited with error

```json
{"success":true, "message":"Your session cannot be prepared.","job_id":job_id,"is_finished":true,"without_error":false,"job_log":"some debugging string for you to trace the progress"}
```

The `is_finished: True`, `without_error: False` setting combination indicates an error state.

##### The job was killed or you provided an invalid job_id

```json
{"success":false, "message":"We lost track the job status, it may be you use the wrong job_id, or our backend has restarted with previous run killed. ","job_id":job_id,"is_finished":false,"without_error":false,"job_log":"some debugging string for you to trace the progress"}
```

With HTTP error code `404`. In practice, the `success: False`, `is_finished:False` settting combination should rarely occur.

### To Kill a Corpus Seeding Job in Progress

We do not enforce a singleton pattern on corpus seeding jobs and in theory multiple runs can process concurrently. However, multiple jobs will likely run out of CPU/memory and cause undefined behavior.

You can attempt to kill a previously scheduled job with a delete request:

```bash
curl --request DELETE \
  --url 'http://HTTPENDPOINT/api/v1/concept_discovery/offline_processing/job?job_id=0c70a96f-b34b-40ab-b588-7a38f7d4b8f3'
```

It will return

```json
{"success":true, "message":"We killed your job.","job_id":job_id}
```

Or

```json
{"success":false, "message":"We cannot kill your job, your job_id is valid but the process is not in running state.","job_id":job_id}
```
With ERROR code `500`.

## Online Processing (Clustering On Demand)

### Clustering Result Format

Please find an example output at [example_oiad_clusters.json](example_oiad_clusters.json). 

### To Fetch Initial Clustering Result (after offline processing/corpus seeding)

We use a special uuid (`00000000-0000-0000-0000-000000000000`) for retrieving the clustering results from corpus seeding.

The results can be fetched with this call: 

```bash
curl --request GET \
  --url 'http://HTTPENDPOINT/api/v1/concept_discovery/clustering/result?job_id=00000000-0000-0000-0000-000000000000'
```

### Reclustering Process

We use an asynchronous API for reclustering because the clustering algorithm does not return instantaneously.

#### Reclustering job submission

```bash
curl --request POST \
  --url 'http://HTTPENDPOINT/api/v1/concept_discovery/clustering/submit' \
  --header 'Content-Type: application/json' \
  --data '{"allowed_words":[],"ontology_metadata":""}'
```

`allowed_words` are the words (or phrases joint by `_`) that you want the clustering algorithm to consider. `ontology_metadata` is the ontology metadata in string form.

It will return

```json
{
  "job_id": "1620326564",
  "message": "Job submitted",
  "success": true
}
```

For simplicity, we continue to use the same job_id (`1620326564`) for all of the following example requests.

#### Reclustering job status

```bash
curl --request GET \
  --url 'http://HTTPENDPOINT/api/v1/concept_discovery/clustering/job?job_id=1620326564'
```

There will be two possible return values:

```json
{
  "is_ready": false,
  "job_id": "1620326564",
  "message": "Your job is still pending.",
  "success": true
}
```

This status means that either the job is still running or it finished with an error. Becuase we don't explicitly track the status of the subprocess, the client should implement a timeout mechanism that assumes the reclustering has failed if the pending status persists for more than 10 minutes. A typical clustering request will finish in 4 minutes.

```json
{
  "is_ready": true,
  "job_id": "1620326564",
  "message": "Your result is ready",
  "success": true
}
```

This means the clustering algorithm has returned with valid results.

#### Get reclustering result

```bash
curl --request GET \
  --url 'http://HTTPENDPOINT/api/v1/concept_discovery/clustering/result?job_id=1620326564'
```

### Rescoring Process

Just like for reclustering, we use an asynchronous API. The service will rescore/rerank the existing clustering results. API calls/responses are similar to the reclustering endpoints.

 #### Rescoring job submission
 
 ```bash
curl --request POST \
  --url 'http://HTTPENDPOINT/api/v1/concept_discovery/rescoring/submit' \
  --header 'Content-Type: application/json' \
  --data '{"ontology_metadata":""}'
```
This time the rescoring endpoint doesn't take a set of allowed words. That's because the rescoring call won't change the set of clusters returned in any way, other than reordering them.


 #### Rescoring job status
 
 ```bash
curl --request GET \
  --url 'http://HTTPENDPOINT/api/v1/concept_discovery/rescoring/job?job_id=d605864b-6ee4-46d2-9bc1-3c117b91f554'
```

#### Get rescoring result

```bash
curl --request GET \
  --url 'http://HTTPENDPOINT/api/v1/concept_discovery/rescoring/result?job_id=d605864b-6ee4-46d2-9bc1-3c117b91f554'
```
