import os, sys, re, datetime, logging

current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir))
sys.path.append(project_root)

import flask
import flask_cors

from similarity.event_and_arg_emb_pairwise.utils.feature_loader import load_features
from similarity.event_and_arg_emb_pairwise.utils.convert_HAC_output_to_tree import convert_HAC_output_to_tree


def main():
    flask_app = flask.Flask(__name__,
                            static_folder=os.path.join(project_root, "similarity", "event_and_arg_emb_pairwise",
                                                       "flask_app", "statics"),
                            static_url_path='')
    flask_cors.CORS(flask_app)

    feature_id_to_features = load_features(
        ["/nfs/raid88/u10/users/hqiu_ad/repos/Hume/expts/covid_2000_pilot.081821/dumping/dumper_1/features.list"])

    trigger_re = re.compile(r"\[(.+)\]")

    hac_path = "/home/hqiu/tmp/hac.out"
    node_id_to_node = convert_HAC_output_to_tree(hac_path)
    for node_id, node in node_id_to_node.items():
        feature = feature_id_to_features.get(node_id, None)
        if feature is not None:
            original_text = feature.aux["originalText"]
            trigger_text = trigger_re.findall(original_text)[0]
            node.aux["original_text"] = original_text
            node.aux["trigger_text"] = trigger_text
            node.name = trigger_text

    @flask_app.after_request
    def _(r):
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

    @flask_app.route("/api/v1/hac_tree", methods=['GET'])
    def _():

        return flask.jsonify(node_id_to_node["root"].to_tree())

    return flask_app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    flask_app = main()
    flask_app.run(host="0.0.0.0", port=5000)
