import re
from datetime import datetime
from typing import List
import  json
class jobJsonVO:
    def __init__(self):
        self.jobId = None
        self.jobName = None
        self.accountUserName = None
        self.status = None
        self.queueName = None
        self.execHosts = None
        self.numProcessors = None
        self.submitTime = None
        self.startTime = None
        self.endTime = None
        self.userGroup = None
        self.workDir = None
        self.userPriority = None
        self.gpuCardNum = None
        self.runningTime = None
        self.formatRunningTime = None
        self.jobProcessorTime = None
        self.jobGpuCardTime = None

    def get_start_time(self):
        return self.startTime

    def set_start_time(self, startTime):
        self.startTime = startTime

    def get_end_time(self):
        return self.endTime

    def set_end_time(self, endTime):
        self.endTime = endTime

    def get_status(self):
        return self.status

    def getNumProcessors(self):
        return  self.numProcessors

    def getRunningTime(self):
        return  self.runningTime
class JobConstants:
    DONE = "DONE"
    EXIT = "EXIT"
    RUN = "RUN"
    PEND = "PEND"
    CANCELLED = "CANCELLED"

def parse_status(status: str) -> str:
    if status == "COMPLETED":
        return JobConstants.DONE
    if status == "FAILED":
        return JobConstants.EXIT
    if status == "RUNNING":
        return JobConstants.RUN
    if status == "PENDING":
        return JobConstants.PEND
    if "CANCELLED" in status:
        return JobConstants.CANCELLED
    return status

def parse_slurm_str_to_str(date_str: str) -> str:
    # Implement your date parsing logic here
    date_str=date_str.replace("T"," ")
    date_str=date_str.replace("Z"," ")
    return date_str

def handle_alloc_tres_get_gpus(tres_str: str) -> int:
    # Implement your GPU card number extraction logic here
    return 0

def calculate_processor_time(job: jobJsonVO) -> float:
    # Implement your processor time calculation logic here
    processors = job.getNumProcessors()
    runningTime = job.getRunningTime()
    processorsRunningTime = processors * runningTime
    return processorsRunningTime

def calculate_gpu_card_time(job: jobJsonVO) -> float:
    # Implement your GPU card time calculation logic here
    return 0.0
def parse_date(date_str: str) -> datetime:
    # 假设这是一个将字符串解析为 datetime 对象的函数
    # 这里使用默认的日期格式,您可以根据实际需求调整
    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
def get_now_date() -> datetime:
    # 返回当前时间的 datetime 对象
    return datetime.now()

def get_running_time(item: jobJsonVO) -> int:
    t = item.get_start_time()
    if t is None:
        return 0

    start_time_temp = parse_slurm_str_to_str(item.get_start_time())
    item.set_start_time(start_time_temp)

    if start_time_temp == "-":
        return 0

    start_time_date = datetime.now()  # 默认值为当前时间
    if item.get_status() != JobConstants.PEND:
        start_time_date = parse_date(start_time_temp)

    running_time = 0
    status = item.get_status()

    if status in [JobConstants.DONE, JobConstants.EXIT]:
        end_time_temp = start_time_temp if item.get_end_time() is None else parse_slurm_str_to_str(item.get_end_time())
        end_time_date = parse_date(end_time_temp)
        item.set_end_time(end_time_temp)
        running_time = int((end_time_date - start_time_date).total_seconds() * 1000)  # 转换为毫秒

    elif status == JobConstants.RUN:
        running_time = int((get_now_date() - start_time_date).total_seconds() * 1000)  # 转换为毫秒

    elif status == JobConstants.CANCELLED:
        end_time_date = parse_date(item.get_end_time()) if item.get_end_time() else start_time_date
        running_time = int((end_time_date - start_time_date).total_seconds() * 1000)  # 转换为毫秒

    elif status == JobConstants.PEND:
        running_time = 0

    return running_time

def format_running_time(job: jobJsonVO) -> str:
    # Implement your running time formatting logic here
    return ""

def process_data(data: dict) -> List[jobJsonVO]:


    try:
        item_list = data["stdout"].split("\n")
        job_json_list = []

        for i in range(len(item_list)):
            if len(item_list) < 1:
                return []

            if i < 1:
                continue

            words = item_list[i].split("|")
            word_list = [word.strip() for word in words if word.strip()]

            if len(word_list) < 14:
                continue

            job_json = jobJsonVO()

            try:
                jobId = int(word_list[0])
            except ValueError:
                continue

            job_json.jobId = word_list[0]
            job_json.jobName = word_list[1]
            job_json.accountUserName = word_list[2]
            job_json.status = parse_status(word_list[3])
            job_json.queueName = word_list[4]
            job_json.execHosts = word_list[5]

            try:
                job_json.numProcessors = int(word_list[6])
                job_json.submitTime = parse_slurm_str_to_str(word_list[7])
                job_json.startTime = parse_slurm_str_to_str(word_list[8])
            except (ValueError, IndexError):
                continue

            if job_json.status == "DONE" or len(word_list) >= 10:
                if word_list[9] != "Unknown":
                    job_json.endTime = parse_slurm_str_to_str(word_list[9])

            job_json.userGroup = word_list[10]
            job_json.workDir = word_list[11]
            job_json.userPriority = int(word_list[12])
            job_json.gpuCardNum = handle_alloc_tres_get_gpus(word_list[13])

            job_json.runningTime = get_running_time(job_json)
            job_json.formatRunningTime = format_running_time(job_json)
            job_json.jobProcessorTime = calculate_processor_time(job_json)
            job_json.jobGpuCardTime = calculate_gpu_card_time(job_json)



            job_dict = job_json.__dict__

            job_json_list.append(job_dict)

        job_json_list.reverse()

        return job_json_list

    except Exception as e:
        print(f"An error occurred: {e}")
        raise Exception("CLUSTER_ERROR")
