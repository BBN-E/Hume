import io
import json
import time

import requests
import serifxml3


def serif_service(HOSTNAME, PORT, doc):
    # HOSTNAME = "afrl102"
    # PORT = 5051
    # content = "Conflict across different parts of the country continues to lead to displacement."

    serif_doc = serifxml3.send_serifxml_document(doc, docid='anonymous', language='English',
                                                 hostname=HOSTNAME, port=PORT,
                                                 end_stage='output', input_type='auto', verbose=False,
                                                 timeout=0, num_tries=1, document_date=None)
    buf = io.BytesIO()
    serif_doc.save(buf)
    buf.seek(0)
    return buf.read()


def nlplingo_service(HOSTNAME, PORT, serif_txt):
    req_buf = list()
    req_buf.append(('serifxmls', ("DUMMY", serif_txt, 'application/xml')))
    r = requests.post("http://{}:{}/prediction_json".format(HOSTNAME, PORT), files=req_buf)
    r = r.json()
    return r


def main():
    SERIF_HOSTNAME = "afrl102"
    SERIF_PORT = 5051
    NLPLINGO_HOSTNAME = "afrl103"
    NLPLINGO_PORT = 5021

    start_time = time.time()
    number_of_events = 0
    with open("/home/hqiu/tmp/sentence.json", 'r') as fp:
        sentences = json.load(fp)
        for content in sentences:
            serif_buf = serif_service(SERIF_HOSTNAME, SERIF_PORT, content)
            prediction_json = nlplingo_service(NLPLINGO_HOSTNAME, NLPLINGO_PORT, serif_buf).get('display_json', dict())
            for event_type, sent_spans in prediction_json.items():
                for possible_trigger in sent_spans.values():
                    possible_trigger = dict(possible_trigger)
                    for trigger in list(filter(lambda x: x.startswith("trigger_"), possible_trigger.keys())):
                        number_of_events += 1
    end_time = time.time()

    print(
        "Len:{}, Duration: {}, Number of triggers: {}".format(len(sentences), end_time - start_time, number_of_events))


if __name__ == "__main__":
    main()
