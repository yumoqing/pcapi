from slurm import sshClient
import  json

def df_to_json(df_output):
    # 解析输出
    lines = df_output.strip().split("\n")
    headers = lines[0].split()
    data = []

    for line in lines[1:]:
        values = line.split()
        entry = {
            headers[0]: values[0],  # filesystem
            headers[1]: values[1],  # type
            headers[2]: values[2],  # size
            headers[3]: values[3],  # used
            headers[4]: values[4],  # avail
            headers[5]: values[5],  # use_percent
            headers[6]: values[6],  # mounted_on
        }
        data.append(entry)
    return  data
def  get_storage_json(point):
    command="df -h --output=source,fstype,size,used,avail,pcent,target"
    if point  is not None:
        command=command+" "+point
    result=sshClient.exec_command(command)
    stdout=result["stdout"]
    print(result)
    result_json=df_to_json(stdout)
    print(result_json)
    return result_json
