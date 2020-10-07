import os,sys,json,time,signal,logging,asyncio
import faust,ssl
current_script_path = __file__
sys.path.append(os.path.realpath(os.path.join(current_script_path,os.path.pardir)))

from multiprocessing import set_start_method

from downstream import create_consumer,start_worker
from main_executor_for_streaming import StreamingProcessor

def create_app_streaming(config,message_handler):
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
    create_consumer(app,config,message_handler)
    return app

def main():
    log_format = '[%(asctime)s] {P%(process)d:%(module)s:%(lineno)d} %(levelname)s - %(message)s'
    try:
        logging.basicConfig(level=logging.getLevelName(os.environ.get('LOGLEVEL', 'INFO').upper()),
                            format=log_format)
        log_level = logging.getLevelName(os.environ.get('LOGLEVEL', 'INFO').upper())
    except ValueError as e:
        logging.error(
            "Unparseable level {}, will use default {}.".format(os.environ.get('LOGLEVEL', 'INFO').upper(),
                                                                logging.root.level))
        log_level = logging.root.leve
    try:
        try:
            os.setpgrp()
        except Exception as e:
            pass
        config_path = "/extra/config.json"
        with open(config_path) as fp:
            config = json.load(fp)
        mini_batch_size = config.get("hume.num_of_vcpus", 8)
        if config.get("hume.streaming.mini_batch_size", None) is not None:
            mini_batch_size = config.get("hume.streaming.mini_batch_size", None)
        mini_batch_wait_time = 30
        if config.get("hume.streaming.mini_batch_wait_time", None) is not None:
            mini_batch_wait_time = config.get("hume.streaming.mini_batch_wait_time", None)
        buffer_space = os.path.join(config['hume.tmp_dir'], 'streaming_tmp')
        streaming_processor = StreamingProcessor(mini_batch_size,mini_batch_wait_time,buffer_space,config_path)
        app = create_app_streaming(config,streaming_processor.kafka_message_handler)
        loop = asyncio.get_event_loop()
        worker = faust.Worker(app, loop=loop, loglevel=log_level)
        try:
            loop.run_until_complete(start_worker(worker))
        finally:
            loop.run_until_complete(worker.stop())
            loop.close()
    finally:
        try:
            pgid = os.getpgid(os.getpid())
            os.killpg(pgid, signal.SIGTERM)
        except Exception as e:
            os.kill(os.getpid(),signal.SIGTERM)

if __name__ == "__main__":
    set_start_method('spawn')
    main()

