from . import sshClient
import  json
'''
创建队列
'''
def create_partition(dict):
    command = "sudo scontrol create "
    for key, value in dict.items():
        command=command+key+"="+str(value)+" "

    print(command)
    return sshClient.exec_command(command)
'''
更新队列
'''
def update_partition(dict):
    command = "sudo scontrol update "
    for key, value in dict.items():
        command=command+key+"="+str(value)+" "

    return sshClient.exec_command(command)

'''
删除队列
'''
def delete_partition(dict):
    command = "sudo scontrol delete  "
    for key, value in dict.items():
        command = command + key + "=" + str(value) + " "

    return sshClient.exec_command(command)
'''
查询队列详情
'''
def list_partition_detail(PartitionName):
    command = "sudo scontrol show part  "
    if PartitionName is not None:
        command = command + PartitionName + " "

    return sshClient.exec_command(command)

'''
查询队列信息简略
'''
def list_partition_info(query):
    command = "sudo sinfo "

    return sshClient.exec_command(command)

'''
查询队列信息简略 带json
'''
def list_partition_detail_json(query):
    command = "scontrol show part "

    if query["partitionName"] is not None:
        command=command+ " "+query["partitionName"]
    result=sshClient.exec_command(command)

    data_str = result["stdout"]
    # 按空行分割字符串,得到每个节点的数据
    partition_data = data_str.strip().split('\n\n')

    # 初始化一个列表来存储所有节点的字典
    partition_list = []

    # 遍历每个节点的数据
    for partition_data in partition_data:
        # 初始化一个字典来存储当前节点的键值对
        partition_dict = {}
        # 按行分割当前节点的数据
        lines = partition_data.strip().split('\n')
        for line in lines:
            # 按空格分割键值对
            key_value_pairs = line.strip().split()

            for pair in key_value_pairs:
                pair_list= pair.split('=')
                if len(pair_list)<2:
                    key=pair_list[0]
                    value=""
                else:
                    key=pair_list[0]
                    value=pair_list[1]
                # 将键和值添加到字典中
                partition_dict[key] = value
        # 将当前节点的字典添加到列表中
        partition_list.append(partition_dict)

    return partition_list
