import datetime
import json
import logging
import os
import subprocess
import sys
import traceback
import uuid

logger = logging.getLogger(__name__)

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir, os.path.pardir))
sys.path.append(project_root)
hume_repo_root = os.path.realpath(os.path.join(project_root, os.path.pardir, os.path.pardir, os.path.pardir))

from werkzeug.utils import secure_filename
import flask, flask_cors

from concept_discovery_offline.logger_wrapper import JobStatusChecker, JobStatus


def get_final_json_path(potential_job_dir):
    return os.path.join(potential_job_dir, "online_service", "expts", "default", "json",
                        "cluster_topn_annotation.json")


def get_final_cbc_path(potential_job_dir):
    return os.path.join(potential_job_dir, "online_service", "expts", "default", "cbc",
                        "cbc.finalClustering")


def create_app(config, previous_stage_2_cache_folder, conda_root, runtime_folder, event_annotation_jsonl,
               trimmed_annotation_npz):
    # Standard API init
    static_folder = os.path.join(project_root, "concept_discovery_online", "statics")
    flask_app = flask.Flask(__name__, static_folder=static_folder,
                            static_url_path='')
    flask_cors.CORS(flask_app)
    os.makedirs(previous_stage_2_cache_folder, exist_ok=True)
    os.makedirs(runtime_folder, exist_ok=True)
    # Generate starting endpoint
    logger.info("Preparing starting clustering result")
    starting_point_json_dir = os.path.join(runtime_folder, "00000000-0000-0000-0000-000000000000",
                                           "online_service/expts/default/json")
    starting_point_cbc_dir = os.path.join(runtime_folder, "00000000-0000-0000-0000-000000000000",
                                          "online_service/expts/default/cbc")
    os.makedirs(starting_point_json_dir, exist_ok=True)
    os.makedirs(starting_point_cbc_dir, exist_ok=True)
    starting_point_json_file_path = get_final_json_path(previous_stage_2_cache_folder)
    starting_point_cbc_file_path = get_final_cbc_path(previous_stage_2_cache_folder)
    if os.path.islink(os.path.join(starting_point_json_dir, os.path.basename(starting_point_json_file_path))):
        os.unlink(os.path.join(starting_point_json_dir, os.path.basename(starting_point_json_file_path)))
    os.symlink(starting_point_json_file_path,
               os.path.join(starting_point_json_dir, os.path.basename(starting_point_json_file_path)))
    if os.path.islink(os.path.join(starting_point_cbc_dir, os.path.basename(starting_point_cbc_file_path))):
        os.unlink(os.path.join(starting_point_cbc_dir, os.path.basename(starting_point_cbc_file_path)))
    os.symlink(starting_point_cbc_file_path,
               os.path.join(starting_point_cbc_dir, os.path.basename(starting_point_cbc_file_path)))

    @flask_app.after_request
    def add_header(r):
        """
        Add headers to both force latest IE rendering engine or Chrome Frame,
        and also to cache the rendered page for 10 minutes.
        """
        r.headers["Cache-Control"] = "public, no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        r.headers['Last-Modified'] = datetime.datetime.now()
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "-1"
        r.headers['Cache-Control'] = 'public, max-age=0'
        return r

    @flask_app.errorhandler(Exception)
    def internal_error(error):
        flask_app.logger.exception(traceback.format_exc())
        msg = {"success": False, "message": "Unhandled exception", "traceback": traceback.format_exc()}
        return flask.jsonify(msg), 500

    # End standard API init

    @flask_app.route("/api/v1/concept_discovery/clustering/submit", methods=["POST"])
    def clustering_submit():
        if flask.request.method == "POST":
            allowed_words = flask.request.json.get("allowed_words", None)
            ontology_metadata = flask.request.json.get("ontology_metadata", None)
            new_job_id = str(uuid.uuid4())
            run_output_dir = os.path.join(runtime_folder, new_job_id)
            os.makedirs(run_output_dir, exist_ok=True)
            if allowed_words is None:
                return flask.jsonify({"message": "Missing `allowed_words` argument", "success": False}), 400
            else:
                saliency_list = os.path.join(run_output_dir, "salient_words.tsv")
                with open(saliency_list, 'w') as wfp:
                    for i in allowed_words:
                        wfp.write("{}\t{}\n".format(i.replace("\t", " ").replace("\n", " ").replace("\r", " "), 0))
            if ontology_metadata is None:
                return flask.jsonify({"message": "Missing `ontology_metadata` argument", "success": False}), 400
            else:
                ontology_metadata_path = os.path.join(run_output_dir, "CompositionalOntology_metadata.yml")
                with open(ontology_metadata_path, 'w') as wfp:
                    wfp.write("{}".format(ontology_metadata))
            subprocess.Popen(
                ["python", os.path.join(project_root, "concept_discovery_shared", 'cbc_pipeline_wrapper.py'),
                 "--previous_stage_2_cache_folder", previous_stage_2_cache_folder, "--saliency_list",
                 saliency_list, "--conda_root", conda_root,
                 "--recluster",
                 "--ontology_metadata_path", ontology_metadata_path,
                 "--hume_repo_root", hume_repo_root, "--output_folder", os.path.join(runtime_folder, new_job_id),
                 "--trimmed_annotation_npz", trimmed_annotation_npz, "--annotation_event_jsonl",
                 event_annotation_jsonl])
            return flask.jsonify({"success": True, "message": "Job submitted", "job_id": new_job_id}), 201

    @flask_app.route("/api/v1/concept_discovery/clustering/job", methods=["GET", "DELETE"])
    def clustering_job_status():
        job_id = flask.request.args.get("job_id")
        if job_id is None:
            return flask.jsonify({"message": "Missing `job_id` argument", "success": False}), 400
        if flask.request.method == "GET":
            potential_job_dir = os.path.join(runtime_folder, secure_filename(job_id))
            if os.path.isdir(potential_job_dir):
                if os.path.isfile(get_final_json_path(potential_job_dir)):
                    return flask.jsonify({"success": True, "message": "Your result is ready", "job_id": job_id,
                                          "is_ready": True}
                                         ), 200
                else:
                    return flask.jsonify({"success": True, "message": "Your job is still pending.", "job_id": job_id,
                                          "is_ready": False}), 200
            else:
                return flask.jsonify({"success": False, "message": "Invalid jobid"}), 404
        elif flask.request.method == "DELETE":
            msg = {"message": "Cannot find your previous job", "success": False}
            return flask.jsonify(msg), 404

    @flask_app.route("/api/v1/concept_discovery/clustering/result", methods=["GET"])
    def clustering_job_result():
        job_id = flask.request.args.get("job_id")
        if job_id is None:
            return flask.jsonify({"message": "Missing `job_id` argument", "success": False}), 400
        potential_job_dir = os.path.join(runtime_folder, secure_filename(job_id))
        if os.path.isfile(get_final_json_path(potential_job_dir)):
            with open(get_final_json_path(potential_job_dir)) as fp:
                clustering_result = json.load(fp)
            return flask.jsonify(
                {"message": "Your result is ready", "clustering_result": clustering_result, "success": True}), 200
        else:
            return flask.jsonify({"message": "Cannot access the clustering result.", "success": False}), 404

    @flask_app.route("/api/v1/concept_discovery/rescoring/submit", methods=["POST"])
    def rescoring_submit():
        if flask.request.method == "POST":
            cluster_job_id = flask.request.args.get("cluster_job_id")
            ontology_metadata = flask.request.json.get("ontology_metadata", None)
            # remaining_clusters = flask.request.json.get("remaining_cluster_ids", None)
            if cluster_job_id is None:
                return flask.jsonify({"message": "Missing `cluster_job_id` argument", "success": False}), 400

            new_job_id = str(uuid.uuid4())
            run_output_dir = os.path.join(runtime_folder, new_job_id)
            os.makedirs(run_output_dir, exist_ok=True)
            cluster_output_dir = os.path.join(runtime_folder, secure_filename(cluster_job_id))

            if ontology_metadata is None:
                return flask.jsonify({"message": "Missing `ontology_metadata` argument", "success": False}), 400
            else:
                ontology_metadata_path = os.path.join(run_output_dir, "CompositionalOntology_metadata.yml")
                with open(ontology_metadata_path, 'w') as wfp:
                    wfp.write("{}".format(ontology_metadata))

            # if remaining_clusters is None:
            #     remaining_clusters_arg = "None"
            # else:
            #     remaining_clusters_path = os.path.join(run_output_dir, "remaining_clusters.txt")
            #     with open(remaining_clusters_path, 'w') as wfp:
            #         for i in remaining_clusters:
            #             wfp.write("{}\n".format(i.replace("\t", "").replace("\n", "").replace("\r", "")))
            #     remaining_clusters_arg = remaining_clusters_path

            subprocess.Popen(
                ["python", os.path.join(project_root, "concept_discovery_shared", 'cbc_pipeline_wrapper.py'),
                 "--previous_stage_2_cache_folder", previous_stage_2_cache_folder, "--previous_cluster_folder",
                 cluster_output_dir, "--saliency_list", "None", "--conda_root", conda_root,
                 "--ontology_metadata_path", ontology_metadata_path,
                 # "--remaining_clusters_file", remaining_clusters_arg,
                 "--hume_repo_root", hume_repo_root, "--output_folder", os.path.join(runtime_folder, new_job_id),
                 "--trimmed_annotation_npz", trimmed_annotation_npz, "--annotation_event_jsonl",
                 event_annotation_jsonl])
            return flask.jsonify({"success": True, "message": "Job submitted", "job_id": new_job_id}), 201

    @flask_app.route("/api/v1/concept_discovery/rescoring/job", methods=["GET", "DELETE"])
    def rescoring_job_status():
        job_id = flask.request.args.get("job_id")
        if job_id is None:
            return flask.jsonify({"message": "Missing `job_id` argument", "success": False}), 400
        if flask.request.method == "GET":
            potential_job_dir = os.path.join(runtime_folder, secure_filename(job_id))
            if os.path.isdir(potential_job_dir):
                if os.path.isfile(get_final_json_path(potential_job_dir)):
                    return flask.jsonify({"success": True, "message": "Your result is ready", "job_id": job_id,
                                          "is_ready": True}
                                         ), 200
                else:
                    return flask.jsonify({"success": True, "message": "Your job is still pending.", "job_id": job_id,
                                          "is_ready": False}), 200
            else:
                return flask.jsonify({"success": False, "message": "Invalid jobid"}), 404
        elif flask.request.method == "DELETE":
            msg = {"message": "Cannot find your previous job", "success": False}
            return flask.jsonify(msg), 404

    @flask_app.route("/api/v1/concept_discovery/rescoring/result", methods=["GET"])
    def rescoring_job_result():
        job_id = flask.request.args.get("job_id")
        if job_id is None:
            return flask.jsonify({"message": "Missing `job_id` argument", "success": False}), 400
        potential_job_dir = os.path.join(runtime_folder, secure_filename(job_id))
        if os.path.isfile(get_final_json_path(potential_job_dir)):
            with open(get_final_json_path(potential_job_dir)) as fp:
                rescoring_result = json.load(fp)
            return flask.jsonify(
                {"message": "Your result is ready", "rescoring_result": rescoring_result, "success": True}), 200
        else:
            return flask.jsonify({"message": "Cannot access the rescoring result.", "success": False}), 404

    @flask_app.route("/api/v1/concept_discovery/offline_processing/submit", methods=["POST"])
    def offline_processing():
        new_job_id = str(uuid.uuid4())
        run_output_dir = os.path.join(runtime_folder, new_job_id)
        os.makedirs(run_output_dir, exist_ok=True)

        relevant_doc_uuids = flask.request.json.get("relevant_doc_uuids", [])
        allowed_words = flask.request.json.get("allowed_words", None)
        ontology_metadata = flask.request.json.get("ontology_metadata", None)

        if allowed_words is None:
            return flask.jsonify({"message": "Missing `allowed_words` argument", "success": False}), 400
        elif len(allowed_words) < 1:
            return flask.jsonify({"message": "len(allowed_words) < 1", "success": False}), 400
        else:
            saliency_list = os.path.join(run_output_dir, "salient_words.tsv")
            with open(saliency_list, 'w') as wfp:
                for i in allowed_words:
                    wfp.write("{}\t{}\n".format(i.replace("\t", " ").replace("\n", " ").replace("\r", " "), 0))

        if ontology_metadata is None:
            return flask.jsonify({"message": "Missing `ontology_metadata` argument", "success": False}), 400
        elif len(ontology_metadata) < 1:
            return flask.jsonify({"message": "len(ontology_metadata) < 1", "success": False}), 400
        else:
            ontology_metadata_path = os.path.join(run_output_dir, "CompositionalOntology_metadata.yml")
            with open(ontology_metadata_path, 'w') as wfp:
                wfp.write("{}".format(ontology_metadata))

        if len(relevant_doc_uuids) < 1:
            return flask.jsonify({"message": "len(relevant_doc_uuids) < 1", "success": False}), 400
        else:
            cdr_job_info_path = os.path.join(run_output_dir, "cdr_job_info.json")
            cdr_job_d = {"doc_uuids": relevant_doc_uuids}
            cdr_job_d["CDR_retrieval"] = None
            cdr_cache_dir = config.get("hume.cdr_cache_dir", None)
            if cdr_cache_dir is None:
                cdr_cache_dir = os.path.join(run_output_dir, "cdrs")
            cdr_job_d["cdr_cache_dir"] = cdr_cache_dir
            if config.get("hume.oiad.use_local_cdrs", False) is False:
                cdr_job_d["CDR_retrieval"] = config["CDR_retrieval"]
                if "auth" in config:
                    cdr_job_d["auth"] = config["auth"]
            with open(cdr_job_info_path, 'w') as wfp:
                json.dump(cdr_job_d, wfp, indent=4, sort_keys=True, ensure_ascii=False)

        commands = [
            "python3", os.path.join(project_root, 'concept_discovery_offline', 'process_corpus_offline_batch.py'),
            "--cdr_job_info", cdr_job_info_path,
            "--hume_repo_root", hume_repo_root,
            "--conda_root", conda_root,
            "--ontology_metadata_path", ontology_metadata_path,
            "--saliency_list", saliency_list,
            "--trimmed_annotation_npz", trimmed_annotation_npz,
            "--event_annotation_jsonl", event_annotation_jsonl,
            "--output_dir", run_output_dir,
            "--previous_stage_2_cache_folder", previous_stage_2_cache_folder,
            "--use_local_mode", "true",
            "--use_regrounding_cache", 'true' if config.get(
                'hume.use_regrounding_cache', False) is True else 'false',
            "--regrounding_cache_path", config.get(
                'hume.regrounding_cache_path', 'NON_EXISTED_PATH')
        ]

        command = " ".join(commands)

        runtime_config_path = os.path.join(run_output_dir, "command.json")
        with open(runtime_config_path, 'w') as wfp:
            json.dump([command], wfp)
        subprocess.Popen(["python3", os.path.join(project_root, 'concept_discovery_offline', 'logger_wrapper.py'),
                          "--runtime_config_json", runtime_config_path, "--output_dir", run_output_dir])

        return flask.jsonify({"success": True, "message": "Job submitted", "job_id": new_job_id}), 201

    @flask_app.route("/api/v1/concept_discovery/offline_processing/job", methods=["GET", "DELETE"])
    def offline_processing_status():
        job_id = flask.request.args.get("job_id")
        if job_id is None:
            return flask.jsonify({"message": "Missing `job_id` argument", "success": False}), 400
        if flask.request.method == "GET":
            potential_job_dir = os.path.join(runtime_folder, secure_filename(job_id))
            if os.path.isdir(potential_job_dir):
                job_status_checker = JobStatusChecker(potential_job_dir)
                if job_status_checker.running_status == JobStatus.FINISHED_WITHOUT_ERROR:
                    return flask.jsonify(
                        {"success": True, "message": "Your session is ready.", "job_id": job_id, "is_finished": True,
                         "without_error": True, "job_log": job_status_checker.job_std})
                elif job_status_checker.running_status == JobStatus.FINISHED_WITH_ERROR:
                    return flask.jsonify(
                        {"success": True, "message": "Your session cannot be prepared.", "job_id": job_id,
                         "is_finished": True, "without_error": False, "job_log": job_status_checker.job_std})
                elif job_status_checker.running_status == JobStatus.UNKNOWN:
                    return flask.jsonify({"success": False,
                                          "message": "We lost track the job status, it may be you use the wrong job_id, or our backend has restarted with previous run killed. ",
                                          "job_id": job_id, "is_finished": False, "without_error": False,
                                          "job_log": job_status_checker.job_std}), 404
                elif job_status_checker.running_status == JobStatus.RUNNING:
                    return flask.jsonify(
                        {"success": True, "message": "Your session is not ready yet.", "job_id": job_id,
                         "is_finished": False, "without_error": False, "job_log": job_status_checker.job_std})
            else:
                return flask.jsonify({"success": False, "message": "Invalid jobid"}), 404
        elif flask.request.method == "DELETE":
            potential_job_dir = os.path.join(runtime_folder, secure_filename(job_id))
            if os.path.isdir(potential_job_dir):
                job_status_checker = JobStatusChecker(potential_job_dir)
                killed = job_status_checker.kill_job()
                if killed:
                    return flask.jsonify({"success": True, "message": "We killed your job.", "job_id": job_id})
                else:
                    return flask.jsonify({"success": False,
                                          "message": "We cannot kill your job, your job_id is valid but the process is not in running state.",
                                          "job_id": job_id}), 500
            else:
                msg = {"message": "Cannot find your previous job", "success": False}
                return flask.jsonify(msg), 404

    return flask_app


if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--config', type=str, required=False, default=None)
    args = arg_parser.parse_args()

    if args.config is not None:
        with open(args.config) as fp:
            config = json.load(fp)
    else:
        config = {
            'CDR_retrieval': "Redacted/dart/api/v1/cdrs",
            'auth': {
                'username': 'Redacted',
                'password': 'Redacted'
            },
            "hume.oiad.use_local_cdrs": True,
            "hume.cdr_cache_dir": "/nfs/raid88/u10/users/hqiu_ad/raw_corpus/wm/15_docs_test",
            "hume.anaconda_root": "/nfs/raid88/u10/users/hqiu_ad/miniconda3",
            "hume.oiad.port": 5061
        }

    runtime_folder = config["hume.oiad.runtime_dir"]
    previous_stage_2_cache_folder = os.path.join(runtime_folder, "previous_stage_2_cache_folder")
    event_annotation_jsonl = "/nfs/raid87/u10/shared/Hume/wm/annotation.ljson"
    trimmed_annotation_npz = "/nfs/raid87/u10/shared/Hume/wm/distilbert-trigger-annotations.npz"
    flask_app = create_app(config, previous_stage_2_cache_folder, config["hume.anaconda_root"], runtime_folder,
                           event_annotation_jsonl, trimmed_annotation_npz)
    flask_app.run(host="::", port=config.get("hume.oiad.port", 5061))

