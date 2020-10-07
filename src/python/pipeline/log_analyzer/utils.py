import enum,datetime

class JobType(enum.Enum):
    sge="sge"
    sge_gpu = "sge_gpu"
    local="local"


def get_job_lines(log_lines,job_type):
    ret = dict()
    if job_type == JobType.sge:
        ret['scheduled_machine'] = log_lines[6]
        ret['started_time'] = log_lines[4]
        ret['possible_end_time'] = log_lines[-1]
    elif job_type == JobType.local:
        ret['scheduled_machine'] = log_lines[2]
        ret['started_time'] = log_lines[0]
        ret['possible_end_time'] = log_lines[-1]
    elif job_type == JobType.sge_gpu:
        ret['scheduled_machine'] = log_lines[9]
        ret['started_time'] = log_lines[7]
        ret['possible_end_time'] = log_lines[-1]
    return ret

def get_job_info_handler(log_lines,job_type):
    parse_line = get_job_lines(log_lines,job_type)
    scheduled_machine = parse_line['scheduled_machine'].strip().split("on machine ")[-1]
    started_time = parse_line['started_time'].strip().split(" newxg started ")[1].split(" +++++++")[0]
    started_time = datetime.datetime.strptime(started_time,"%c")
    possible_end_time = None
    if "+++++++ newxg finished successfully at " in parse_line['possible_end_time'].strip():
        possible_end_time = parse_line['possible_end_time'].strip().split("+++++++ newxg finished successfully at ")[1].split(" on machine ")[0]
        possible_end_time = datetime.datetime.strptime(possible_end_time,"%c")
    return scheduled_machine,started_time,possible_end_time

def get_job_info(log_lines):
    if "gpuprolog" in log_lines[0].strip():
        return get_job_info_handler(log_lines,JobType.sge_gpu)
    elif "prolog.pl" in log_lines[0].strip():
        return get_job_info_handler(log_lines,JobType.sge)

    return get_job_info_handler(log_lines,JobType.local)