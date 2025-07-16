from . import sshClient

'''
获取节点详情
'''
def get_node_details_json(NodeName):
    command = "scontrol show node "

    if NodeName is  not None:
        command=command+NodeName

    print(command)

    result= sshClient.exec_command(command)
    data_str=result["stdout"]
    # 按空行分割字符串,得到每个节点的数据
    nodes_data = data_str.strip().split('\n\n')

    # 初始化一个列表来存储所有节点的字典
    nodes_list = []

    # 遍历每个节点的数据
    for node_data in nodes_data:
        # 初始化一个字典来存储当前节点的键值对
        node_dict = {}
        # 按行分割当前节点的数据
        lines = node_data.strip().split('\n')
        for line in lines:
            if "OS" in line:
                node_dict["OS"]=line.split("=")[1]
            else:
                # 按空格分割键值对
                key_value_pairs = line.strip().split()
                for pair in key_value_pairs:
                    pair_list= pair.split('=')
                    if len(pair_list) < 2:
                        key=pair_list[0]
                        value=""
                    else:
                        key=pair_list[0]
                        value=pair_list[1]
                    # 将键和值添加到字典中
                    node_dict[key] = value
        # 将当前节点的字典添加到列表中
        nodes_list.append(node_dict)
    return nodes_list

def update_node(dict_data):
    command="sudo scontrol update"
    if dict_data["NodeName"] is not None:
        command=command+" "+"NodeName="+dict_data["NodeName"]
        command=command+" "+"State="+dict_data["State"]
        command=command+" "+"Reason="+dict_data["Reason"]

    result= sshClient.exec_command(command)
    return result

