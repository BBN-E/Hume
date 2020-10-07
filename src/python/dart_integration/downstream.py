import os
import json
import ssl
from pathlib import Path
from faust import Record, StreamT, Worker
import faust
import requests
import shutil
import asyncio
import logging
from multiprocessing import Process, Manager
def write_cdr(persist_dir, key, value):
    os.makedirs(persist_dir,exist_ok=True)
    persist = Path(persist_dir) / (key + '.txt')
    value = value.dumps().decode() if isinstance(value, Record) else json.dumps(value)
    persist.write_text(value)


def create_consumer(app,config,callback):
    # create topics
    stream_out_topic = app.topic(config['topic']['from'], key_type=str, value_type=str)

    # create an agent subscribed to the stream.out topic. this function
    # receives events, updates them, and then prints the event to stdout
    @app.agent(stream_out_topic)
    async def stream_out(stream: StreamT):
        """Print the events to stdout"""
        auto_commit = config['app'].get('enable_auto_commit', False)
        events = stream.events() if auto_commit else stream.noack().events()
        async for event in events:
            print(f'persisting {event.key}')
            callback(os.path.join(config['hume.tmp_dir'],'kafka_msgs'), event.key, event.value)
            yield event

def create_app_batching(config):
    broker = None
    if config.get('kafka.bootstrap.servers'):
        broker = f'kafka://{config["kafka.bootstrap.servers"]}',

    broker_credentials = None
    if 'auth' in config:
        broker_credentials = faust.SASLCredentials(
            username=config['auth']['username'],
            password=config['auth']['password'],
            ssl_context=ssl.create_default_context()
        )

    # create your application
    app = faust.App(
        config['app']['id'],
        broker=broker,
        broker_credentials=broker_credentials,
        consumer_auto_offset_reset=config['app'].get('auto_offset_reset', None),
        stream_wait_empty=config['app'].get('enable_auto_commit', None),
        topic_disable_leader=True
    )
    create_consumer(app,config,write_cdr)
    return app


async def start_worker(worker: Worker) -> None:
    await worker.start()

def kafka_consumer_batching_main(config_path):
    with open(config_path) as fp:
        config = json.load(fp)
    shutil.rmtree(os.path.join(config['hume.tmp_dir'],'kafka_msgs'),ignore_errors=True)
    shutil.rmtree(os.path.join(config['hume.tmp_dir'],'cdrs_tmp'),ignore_errors=True)
    app = create_app_batching(config)
    logging.basicConfig(level=logging.getLevelName(os.environ.get('LOGLEVEL', 'INFO')))
    loop = asyncio.get_event_loop()
    worker = Worker(app, loop=loop,loglevel=logging.getLevelName(os.environ.get('LOGLEVEL', 'INFO')))
    try:
        loop.run_until_complete(start_worker(worker))
    finally:
        loop.run_until_complete(worker.stop())
        loop.close()



def cdr_retrive_batching(config_path):
    with open(config_path) as fp:
        config = json.load(fp)
    message_dir = os.path.join(config['hume.tmp_dir'],'kafka_msgs')
    cdr_storage_dir_tmp = os.path.join(config['hume.tmp_dir'],'cdrs_tmp')
    cdr_endpoint = config['CDR_retrieval']
    # shutil.rmtree(cdr_storage_dir_tmp,ignore_errors=True)
    os.makedirs(cdr_storage_dir_tmp,exist_ok=True)
    if os.path.exists(message_dir):
        for file in os.listdir(message_dir):
            p = os.path.join(message_dir,file)
            msg_id = file[:-len(".txt")]
            if os.path.exists(os.path.join(cdr_storage_dir_tmp,"{}.json".format(msg_id))) is False:
                with open(p) as fp:
                    msg = json.load(fp)
                msg_body = json.loads(msg["cdr-data"])
                uuid = msg_body['document_id']
                if "extracted_text" not in msg_body:
                    continue
                uri = "{}/{}".format(cdr_endpoint,uuid)
                try:
                    r = requests.get(uri)
                    cdr = r.json()
                    with open(os.path.join(cdr_storage_dir_tmp, "{}.json".format(msg_id)), 'w') as fp2:
                        json.dump(cdr, fp2, indent=4, sort_keys=True, ensure_ascii=False)
                    logging.root.info("Saving cdr for message {}".format(msg_id))
                except:
                    import traceback
                    traceback.print_exc()


if __name__ == "__main__":
    import sys
    config_path = sys.argv[1]
    with open(config_path) as fp:
        config = json.load(fp)
    with Manager() as manager:
        p = Process(target=kafka_consumer_batching_main, args=(config_path,))
        p.start()
        p.join(config.get("hume.batching.kafka_timeout",60))
        p.terminate()
    cdr_retrive_batching(config_path)
