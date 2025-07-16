from . import  parse_job

from  . import  sshClient
import json



def get_history_job_command(query):
    command="sacct -a  -p "
    if "startStartTime" in query:
        command=command+"-S "+query["startStartTime"]+" "
    if "group" in query:
        command=command+"-g "+query["group"]+" "
    if "jobId" in query:
        command=command+"-j "+query["jobId"]+" "
    if "accountUserName" in query:
        command=command+"-u "+query["accountUserName"]+" "
    if "jobIdList" in query:
        command = command + "-j"
        for jobId in query["jobIdList"]:
            command=command+"-j "+jobId+" "

    command=command+"--format=JobId,JobName%30,User%50,state,partition,NodeList,AllocCPUS,Submit,Start,End,Group,Workdir%100,Priority,ReqTRES%50"+" "
    command=command+" "+"-X"
    return command

'''
获取历史作业
'''
def get_history_list(data):
    command=get_history_job_command(data)

    return sshClient.exec_command(command)


def get_history_list_json(data):
    result=get_history_list(data)
    result_json=parse_job.process_data(result)
    return result_json



'''
提交作业
'''
def submit_job(command):
    command=command.replace("\r"," ")
    return sshClient.exec_command(command)


'''
恢复作业
'''
def resume_job(jobId):
    command="sudo scontrol resume  "+jobId
    return sshClient.exec_command(command)


'''
挂起作业
'''
def suspend_job(jobId):
    command="sudo scontrol suspend  "+jobId
    return sshClient.exec_command(command)


'''
杀掉作业
'''
def kill_job(jobId):
    command="sudo scancel  "+jobId
    return sshClient.exec_command(command)
'''
获取实时作业
'''
def get_real_time_list(query):
    command="squeue -a "
    return sshClient.exec_command(command)
'''
获取实时作业
'''
def get_real_time_list_json(query):
    command="squeue -a --json"
    result= sshClient.exec_command(command)
    std_out=result["stdout"]
    std_out=json.loads(std_out)
    return std_out