import argparse
import json
import os
import sys

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir, os.path.pardir))
sys.path.append(project_root)

from Grounder import ServiceGrounder


def create_app(config_path):
    import flask
    app = flask.Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    with open(config_path) as fp:
        config = json.load(fp)

    #grounding_list_dir = config['grounding_list_dir']
    internal_yaml = config['internal_ontology_yaml']
    embeddings_file = config["embeddings_file"]
    minimum_groundings = config["min_groundings"]
    threshold = config["threshold"]
    external_yaml = config["external_ontology_yaml"]
    internal_exemplars_json = config["exemplars_json"]

    grounder = ServiceGrounder(
        external_yaml,
        minimum_groundings,
        threshold,
        embeddings_file,
        internal_yaml,
        internal_exemplars_json
    )

    @app.errorhandler(Exception)
    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(405)
    def exceptionHandler(error):
        code = getattr(error, 'code', 500)
        return flask.jsonify({"status": "ERROR"}), code

    @app.before_first_request
    def init():
        grounder.load_model()

    @app.route('/get_grounding', methods=['POST'])
    def get_prediction_json():
        try:
            ret = grounder.query_grounding(flask.request.json.get('mentions'),
                                           flask.request.json.get('ontology')
                                           )
            return flask.jsonify({'status': "SUCCESS", 'groundings': ret, 'msg': "OK"}), 200
        except:
            import traceback
            traceback.print_exc()
            return flask.jsonify({'status': 'ERROR', 'msg': traceback.format_exc()}), 500

    return app


parser = argparse.ArgumentParser()
parser.add_argument('--runtime', required=True)
args = parser.parse_args()
runtime = args.runtime
app = None
if runtime == "dev":
    app = create_app(os.path.join(project_root, 'config', 'dev.json'))
else:
    app = create_app(os.path.join(project_root, 'config', 'production.json'))


if __name__ == "__main__":
    app.run("0.0.0.0", 5062)
