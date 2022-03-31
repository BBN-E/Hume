import os
import json
import subprocess
import shlex
import argparse
import enum

def run_command(command, pgid, output_dir=None):
    out_fp = None
    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        out_fp = open(os.path.join(output_dir, "std"), 'w')
    process = subprocess.Popen(shlex.split(command), stdout=out_fp, stderr=out_fp)
    with open(os.path.join(output_dir, 'pgid'), 'w') as wfp:
        wfp.write("{}".format(pgid))
    with open(os.path.join(output_dir, 'pid'), 'w') as wfp:
        wfp.write("{}".format(process.pid))
    process.wait()
    rc = process.poll()
    with open(os.path.join(output_dir,'returncode'),'w') as wfp:
        wfp.write("{}".format(process.returncode))
    if output_dir is not None:
        out_fp.close()
    return process

def check_process_liveness(pid):
    """ Check For the existence of a unix pid.
    https://stackoverflow.com/a/568285/6254393
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

class JobStatus(enum.Enum):
    RUNNING = enum.auto()
    FINISHED_WITH_ERROR = enum.auto()
    FINISHED_WITHOUT_ERROR = enum.auto()
    UNKNOWN = enum.auto()

class JobStatusChecker(object):
    def __init__(self,job_control_dir):
        self.job_control_dir = job_control_dir

    @property
    def pid(self):
        try:
            with open(os.path.join(self.job_control_dir, 'pid')) as fp:
                pid = int(fp.read())
            return pid
        except:
            return None

    @property
    def return_code(self):
        try:
            with open(os.path.join(self.job_control_dir, 'returncode')) as fp:
                return int(fp.read())
        except:
            return None

    @property
    def running_status(self):
        if self.pid is None:
            return JobStatus.UNKNOWN
        is_running = check_process_liveness(self.pid)
        if is_running:
            return JobStatus.RUNNING
        else:
            if self.return_code == 0:
                return JobStatus.FINISHED_WITHOUT_ERROR
            else:
                return JobStatus.FINISHED_WITH_ERROR

    @property
    def job_std(self):
        if os.path.isfile(os.path.join(self.job_control_dir, 'std')):
            with open(os.path.join(self.job_control_dir, 'std')) as fp:
                return fp.read()
        return ""

    def kill_job(self):
        if self.running_status == JobStatus.RUNNING:
            with open(os.path.join(self.job_control_dir,'pgid')) as fp:
                pgid = int(fp.read())
                os.killpg(pgid, 9)
            return True
        else:
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime_config_json")
    parser.add_argument("--output_dir")
    args = parser.parse_args()
    with open(args.runtime_config_json) as fp:
        command = json.load(fp)[0]
    os.setsid()
    pgid = os.getpgid(os.getpid())
    run_command(command, pgid, args.output_dir)
