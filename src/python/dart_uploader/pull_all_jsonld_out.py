import json
import os
import shutil


def export_serialization_into_single_folder(serialization_folder, output_folder):
    for root, dirs, files in os.walk(serialization_folder):
        for file in files:
            if file.endswith(".json-ld"):
                with open(os.path.join(root, file), encoding='utf-8') as fp:
                    j = json.load(fp)
                    assert len(j['documents']) == 1
                    doc_uuid = j['documents'][0]['@id']
                shutil.copy(os.path.join(root, file), os.path.join(output_folder, "{}.json-ld".format(doc_uuid)))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--serialization_folder', required=True)
    parser.add_argument('--output_folder', required=True)
    args = parser.parse_args()
    export_serialization_into_single_folder(args.serialization_folder, args.output_folder)
