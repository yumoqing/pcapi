import json
import yaml
import os
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from os.path import expanduser
from kubernetes import client, config
from kubernetes.client import ApiException
from . import k8s_utils_linuxos_ubuntu, k8s_utils_relationaldb_mysql, parse_k8s_params
from . import ssh_utils,k8s_utils_public
from appPublic.log import debug
import traceback

async def delete_cluster_node(params):
    """
    删除集群节点
    --namespace 或 -n:指定节点所在的命名空间。不过,节点是集群级别的资源,不隶属于特定的命名空间,所以此参数一般不用于删除节点。
    --force:当节点处于不可达状态或者无法正常响应时,可以使用 --force 参数强制删除节点
        kubectl delete node <node-name> --force
    --grace-period:指定节点在被强制终止之前的宽限期（以秒为单位）。默认值是 30 秒,设置为 0 表示立即强制删除。一般和 --force 一起使用
        kubectl delete node <node-name> --force --grace-period=0
    在删除节点之前,需要先将节点标记为不可调度(Cordon),并将节点上的 Pod 安全地迁移到其他节点(Drain)
    将节点标记为不可调度,防止新的 Pod 被调度到该节点
        kubectl cordon <node-name>
    排空节点上的 Pod,将它们迁移到其他节点
        kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data --ignore-not-found
    --ignore-daemonsets:忽略 DaemonSet 创建的 Pod,因为 DaemonSet 会确保每个节点上都运行一个 Pod 副本,这些 Pod 不需要迁移。
    --delete-emptydir-data:删除节点上 EmptyDir 卷中的数据,EmptyDir 卷是临时存储,删除节点时数据会丢失
    --ignore-not-found:如果指定的节点不存在,忽略错误,不会报错退出
    """
    return "delete_cluster_node ok"

async def node_state_switch(params):
    """
    恢复节点：
        kubectl uncordon 命令将节点标记为可调度状态,这样调度器就会重新考虑将新的 Pod 分配到该节点上
        kubectl uncordon worker-node-1
    暂停节点：
        kubectl cordon 命令将节点标记为不可调度状态,这样调度器就不会将新的 Pod 分配到该节点上
        kubectl cordon worker-node-1
    （可选）排空节点上的 Pod
        kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
    """
    return "node_state_switch ok"

async def yaml_apply_delete(params):
    """
        1. 通过cpcc传递过来的参数进行级联初始化资源实例;
        2. 通过cpcc传递过来的参数进行级联更新资源实例;
        3. 通过cpcc传递过来的参数进行级联删除资源实例;
    """
    # 为了更好支持多种资源实例类型（操作系统/关系型/非关系型数据库等每种资源实例类型单开逻辑便于维护）
    instance_type = params.get("instance_type")
    if instance_type == "RelationalDB":
        k8s_utils_relationaldb_mysql.handle_k8s_operations(params)
    # if instance_type == "RelationalDB_PostgreSQL":
    #     k8s_utils_relationaldb_mysql.handle_k8s_operations(params)
    elif instance_type == "LinuxOS":
        k8s_utils_linuxos_ubuntu.handle_k8s_operations(params)

async def node_label_opt(params):
    """
        要设置节点 worker-node-1 上的标签 app,可以使用以下命令：
        kubectl label nodes worker-node-1 app=app,注意标签键和值之间有一个等号 (=),表示设置该标签。

        要取消节点 worker-node-1 上的标签 app,可以使用以下命令：
        kubectl label nodes worker-node-1 app-，注意标签键后面有一个短横线 (-),表示取消该标签。

        设置/解绑标签后,调度器将考虑该标签进行 Pod 调度,可以使用该标签来选择特定的节点。
        设置/解绑标签不会影响节点上已经运行的 Pod,它们仍然会继续运行。 
    """
    host = params.get("host")
    port = int(params.get("port"))
    username = params.get("user")
    password = params.get("password")
    worker_node = params.get("worker_node")
    label = params.get("label")
    opt = params.get("opt")
    if opt == "label":
        get_cluster_node_cmd = [f"kubectl label nodes {worker_node} {label} --overwrite"]
        debug(f'绑定标签命令: {get_cluster_node_cmd}')
        if username != "root":
            results = ssh_utils.ssh_execute_command_noroot(host, port, username, password, 
                                                           get_cluster_node_cmd, sudo_timeout=10)  # 设置标签可能需要一些时间
        else:
            results = ssh_utils.ssh_execute_command(host, port, username, password, get_cluster_node_cmd)    
        overwrite_info = results[0][0].strip()
        if "not labeled" in overwrite_info:
            raise f"{worker_node} 绑定标签 {label} 失败,请检查集群节点状态或标签是否已绑定?"
        else:
            return f"{worker_node} 绑定标签 {label} 成功!"
    elif opt == "unlabel":
        get_cluster_node_cmd = [f"kubectl label nodes %s %s-" % (worker_node,label.split('=')[0])]
        debug(f'解绑标签命令: {get_cluster_node_cmd}')
        if username != "root":
            results = ssh_utils.ssh_execute_command_noroot(host, port, username, password,
                                                            get_cluster_node_cmd, sudo_timeout=10)   # 取消标签可能需要一些时间
        else:
            results = ssh_utils.ssh_execute_command(host, port, username, password, get_cluster_node_cmd)
        # debug(f'解绑标签结果: {results}')
        overwrite_info = results[0][0].strip()
        if "unlabeled" in overwrite_info or overwrite_info == "":
            return f"{worker_node} 解绑标签 {label} 成功!"
        else:
            raise f"{worker_node} 解绑标签 {label} 失败,请检查集群节点状态或标签是否已绑定?"
    
async def unset_node_label(params):
    """
    要取消节点 worker-node-1 上的标签 app,可以使用以下命令：
    kubectl label nodes worker-node-1 app-，注意标签键后面有一个短横线 (-),表示取消该标签。
    取消标签后,节点将不再具有该标签,调度器将不再考虑该标签进行 Pod 调度。
    取消标签不会影响节点上已经运行的 Pod,它们仍然会继续运行。
    """
    host = params.get("host")
    port = int(params.get("port"))
    username = params.get("user")
    password = params.get("password")
    worker_node = params.get("worker_node")
    label = params.get("label")
    

async def get_cluster_nodes_by_server(params):
    host = params.get("host")
    port = int(params.get("port"))
    username = params.get("user")
    password = params.get("password")
    get_cluster_node_cmd = ["kubectl get nodes -o wide --show-labels"]
    if username != "root":
        results = ssh_utils.ssh_execute_command_noroot(host, port, username, password, 
                                                       get_cluster_node_cmd, sudo_timeout=10)
    else:
        results = ssh_utils.ssh_execute_command(host, port, username, password, get_cluster_node_cmd)
    parse_k8s_nodes_result = results[0][0].strip()
    parse_k8s_nodes_result = parse_k8s_params.parse_k8s_nodes(parse_k8s_nodes_result)
    # debug(f'集群 {host=} 所有节点信息如下{results=} => 转换后:\n{parse_k8s_nodes_result=}')
    return parse_k8s_nodes_result

async def get_cluster_pods_by_kubeconfig(params):
    """
        通过调用方传递来的kubeconfig信息
        获取集群中所有资源实例(Pod)信息详情
    """
    kubeconfig = params.get("kubeconfig")
    return k8s_utils_public.get_pod_info(kubeconfig)

async def determine_accommodat_by_kubeconfig(params):
    """
        通过调用方传递来的kubeconfig信息
        判断集群中可部署哪些部件组合n
        返回的是产品ID列表
    """
    # debug(f'=====determine_accommodat_by_kubeconfig params: {params}')
    kubeconfig = params.get("kubeconfig")
    resources = params.get("resources", {})
    # debug(f'=====kubeconfig: {kubeconfig}, resources: {resources}')
    return k8s_utils_public.determine_accommodat(kubeconfig, resources)

async def get_cluster_nodes_by_kubeconfig(params):
    """
        通过调用方传递来的kubeconfig信息
        获取集群中所有节点信息详情
    """
    kubeconfig = params.get("kubeconfig")
    return k8s_utils_public.get_node_info(kubeconfig)

async def get_cluster_pods_by_server(params):
    host = params.get("host")
    port = int(params.get("port"))
    username = params.get("user")
    password = params.get("password")
    # get_cluster_node_cmd = ["kubectl get pods --all-namespaces -o wide"]
    get_cluster_pod_cmd = ["kubectl get pods --all-namespaces -o wide | grep -Ev 'kube-flannel|kube-system'"]
    if username != "root":
        results = ssh_utils.ssh_execute_command_noroot(host, port, username, password, 
                                                       get_cluster_pod_cmd, sudo_timeout=10)
    else:
        results = ssh_utils.ssh_execute_command(host, port, username, password, get_cluster_pod_cmd)
    parse_k8s_pods_result = results[0][0].strip()
    parse_k8s_pods_result = parse_k8s_params.parse_k8s_pods(parse_k8s_pods_result)
    # debug(f'集群 {host=} 所有Pod信息如下{results=} => 转换后:\n{parse_k8s_pods_result=}')
    return parse_k8s_pods_result

async def new_cluster_install(params):
    # 随后填充远程操控k8s主逻辑
    """
        用于接收cpcc端传递过来的k8s安装指令参数, 进行远程sshx调用操作内网机器进行集群节点的安装
        可以安装控制节点和工作节点
        参数示例：
        {'cluster_type': '0', 'host': '192.168.0.3', 'port': '22', 'user': 'ysh', 'password': 'Kyy@123456'}
    """
    debug(f'=====new_cluster_install params: {params}')
    host = params.get("host")
    port = int(params.get("port"))
    username = params.get("user")
    password = params.get("password")
    role = params.get("role")
    target_file_path = "/opt/k8s_install.sh"
    local_file_path="script/k8s_install.sh"
    scp_map = {
            local_file_path: target_file_path,
            "files/kube-flannel.yml":"/opt/kube-flannel.yml",
            "files/components.yaml":"/opt/components.yaml",
            "files/ingress-nginx-controller.yaml":"/opt/ingress-nginx-controller.yaml",
            "files/storage_class.yaml":"/opt/storage_class.yaml",
            # "files/nfs-provisioner-deploy.yaml":"/opt/nfs-provisioner-deploy.yaml",
            "files/nfs-rbac.yaml": "/opt/nfs-rbac.yaml",
            "files/config.toml": "/opt/config.toml",
            "files/nvidia-device-plugin.yml": "/opt/nvidia-device-plugin.yml",
            "files/libnvidia-container-tools_1.17.8-1_amd64.deb": "/opt/libnvidia-container-tools_1.17.8-1_amd64.deb",
            "files/libnvidia-container1_1.17.8-1_amd64.deb": "/opt/libnvidia-container1_1.17.8-1_amd64.deb",
            "files/nvidia-container-toolkit_1.17.8-1_amd64.deb": "/opt/nvidia-container-toolkit_1.17.8-1_amd64.deb",
            "files/nvidia-container-toolkit-base_1.17.8-1_amd64.deb": "/opt/nvidia-container-toolkit-base_1.17.8-1_amd64.deb",
            "script/k8s_uninstall.sh": "/opt/k8s_uninstall.sh",
            "script/import_images.sh": "/opt/import_images.sh",
            }
    # 此处如果是工作节点的话应该完成
    nfs_server_ip = host if role == "master" else str()
    nfs_share_path = "/k8sdata" if role == "master" else str()
    install_clusterrole_command = ["chmod 755 %s" % target_file_path,"%s %s %s %s" % (target_file_path,role,nfs_server_ip,nfs_share_path)]
    debug(f'{install_clusterrole_command=}')
    try:
        if username == "root":
            # 如果是root用户,直接执行安装脚本
            debug(f'开始Root用户安装集群节点,用户名: {username}, 角色: {role},主机: {host},端口: {port}')
            await ssh_utils.ssh_execute_command(host, port, username, password, 
                                    install_clusterrole_command, real_time_log=True,
                                    scp_map=scp_map)
        else:
            # 如果是普通用户,需要先将处理好
            debug(f'开始普通用户安装集群节点,用户名: {username}, 角色: {role},主机: {host},端口: {port}')
            await ssh_utils.ssh_execute_command_noroot(host, port, username, password, 
                                    install_clusterrole_command, real_time_log=True,
                                    scp_map=scp_map,
                                    sudo_timeout=500)  # 设置较长的超时时间，适应K8s安装过程
    except:
        # debug(f"集群节点安装失败:{traceback.format_exc()}")
        raise traceback.format_exc()
    results = "%s => %s节点安装成功" % (host,role)
    if role == "master":
        # 安装控制节点接口,一共分三步：
        # 第一步：执行安装命令
        # 第二步：获取集群工作节点加入凭证
        # 第三步：返回加入凭证给cpcc保存（pcapi无状态）
        clusterauth_command = ['kubeadm token create --print-join-command --ttl 0']
        if username != "root":
            join_idp = await ssh_utils.ssh_execute_command_noroot(host, port, username, password, clusterauth_command,
                                                             real_time_log=True, sudo_timeout=60)  # 获取token命令应该较快完成
        else:
            join_idp = await ssh_utils.ssh_execute_command(host, port, username, password, clusterauth_command, real_time_log=True)
        join_idp = join_idp[0][0].strip()
        debug(f'集群验证码:{join_idp=}')
        kubeconfig_context_command = ['cat /root/.kube/config']
        if username != "root":
            kubeconfig = await ssh_utils.ssh_execute_command_noroot(host, port, username, password, 
                                                              kubeconfig_context_command, real_time_log=True, 
                                                              sudo_timeout=60)  # 获取kubeconfig命令应该较快完成
        else:
            kubeconfig = await ssh_utils.ssh_execute_command(host, port, username, password, kubeconfig_context_command, real_time_log=True)
        kubeconfig = kubeconfig[0][0].strip()
        debug(f'集群上下文:{kubeconfig=}')
        results = join_idp + "###" + kubeconfig
    if role == "worker":
        # 安装工作节点接口,一共分两步：
        # 第一步：执行安装命令
        # 第二步：通过传进来的加入命令加入集群
        debug(f'开始工作节点加入集群')

        join_command = params.get("join_command")
        if username != "root":
            await ssh_utils.ssh_execute_command_noroot(host, port, username, password, [join_command], 
                                                 real_time_log=True, sudo_timeout=120)  # 工作节点加入可能需要一些时间
        else:
            await ssh_utils.ssh_execute_command(host, port, username, password, [join_command], real_time_log=True)
        
    return results

async def get_multiple_cluster_pod():
    """
    获取 kubeconfig 中所有集群的 Pod 信息（JSON 格式）
    
    功能：
    1. 遍历 kubeconfig 中所有上下文（集群）
    2. 对每个集群获取所有命名空间的 Pod 信息
    3. 返回格式化的 JSON 结果
    
    返回值：
    str: 格式化的 JSON 字符串,结构示例：
    {
        "cluster1": [
            {"ip": "10.0.0.1", "namespace": "default", "name": "pod1"},
            ...
        ],
        "cluster2": [...]
    }
    """
    # 获取所有集群上下文（忽略当前激活状态）
    contexts, _ = config.list_kube_config_contexts()
    if not contexts:
        print("未找到任何集群上下文")
        return

    all_clusters_pods = {}  # 存储所有集群的 Pod 信息

    for context in contexts:
        cluster_name = context["name"]
        try:
            # 创建集群专属的 API 客户端
            api_client = config.new_client_from_config(context=cluster_name)
            v1 = client.CoreV1Api(api_client)
            
            # 收集当前集群的 Pod 信息
            pods = []
            for pod in v1.list_pod_for_all_namespaces().items:
                pods.append({
                    "ip": pod.status.pod_ip,
                    "namespace": pod.metadata.namespace,
                    "name": pod.metadata.name
                })
            
            all_clusters_pods[cluster_name] = pods

        except Exception as e:
            print(f"集群 {cluster_name} 访问失败: {str(e)}")

    return all_clusters_pods


async def get_multiple_cluster():
    """
    获取所有集群的完整信息,包括用户证书、RBAC状态、服务账号颁发者等。

    该函数会遍历kubeconfig文件中的所有上下文,针对每个上下文对应的集群进行以下操作：
    1. 从kubeconfig配置中提取静态信息,如API服务器地址、CA证书数据、用户证书和私钥数据。
    2. 通过Kubernetes API获取动态信息,如节点数量、Kubernetes版本、RBAC是否启用以及服务账号颁发者（如果是OIDC集群）。
    3. 处理在配置解析和API调用过程中可能出现的错误,并将错误信息记录在结果中。

    返回格式示例：
    {
        "cluster1": {
            "context_name": "ctx1",
            "api_server": "https://1.1.1.1:6443",
            "ca_cert_data": "LS0tLS1CRUd...",
            "user_cert_data": "LS0tLS1CRUd...",
            "user_key_data": "LS0tLS1CRUd...",
            "nodes_count": 3,
            "notready_count": 0,
            "version": "1.28.3",
            "rbac_enabled": true,
            "service_account_issuer": "https://oidc.example.com",
            "error": null
        }
    }
    """
    try:
        config.load_kube_config()
        contexts, _ = config.list_kube_config_contexts()

        if not contexts:
            return json.dumps({"error": "未找到任何集群上下文信息"}, indent=4)

        # 直接读取 kubeconfig 文件获取原始配置
        kubeconfig_path = expanduser("~/.kube/config")
        with open(kubeconfig_path, 'r') as f:
            config_dict = yaml.safe_load(f)

        clusters_config = config_dict.get('clusters', [])
        users_config = config_dict.get('users', [])

        all_clusters_info = {}
        for context in contexts:
            cluster_name = context['context']['cluster']
            user_name = context['context'].get('user')
            context_name = context['name']  # 新增：获取上下文名称

            cluster_info = {
                'nodes_count': 0,
                'notready_nodes': 0,
                'k8s_version': '',
                'error': None,
                'server_url': '',
                'context_name': context_name,  # 新增字段
                'user_info': {
                    'name': '',
                    'client_certificate': 'not_support',
                    'client_key': 'not_support',
                    'token': 'not_support'
                }
            }

            # 提取 serverUrl 和用户信息
            cluster_config = next(
                (c for c in clusters_config if c['name'] == cluster_name),
                {}
            )
            cluster_info['server_url'] = cluster_config.get('cluster', {}).get('server', '')

            user_config = next(
                (u for u in users_config if u['name'] == user_name),
                {}
            )
            user_data = user_config.get('user', {})

            # 填充用户信息
            cluster_info['user_info']['name'] = user_config.get('name', '')
            # cluster_info['user_info']['client_certificate'] = user_data.get('client-certificate-data', '')
            # cluster_info['user_info']['client_key'] = user_data.get('client-key-data', '')
            # cluster_info['user_info']['token'] = user_data.get('token', '')

            try:
                api_client = config.new_client_from_config(context=context['name'])
                v1 = client.CoreV1Api(api_client)
                version_api = client.VersionApi(api_client)

                nodes = v1.list_node().items
                cluster_info['nodes_count'] = len(nodes)

                notready_nodes = 0
                for node in nodes:
                    ready_condition = next(
                        (cond for cond in node.status.conditions 
                         if cond.type == "Ready" and cond.status == "True"),
                        None
                    )
                    if not ready_condition:
                        notready_nodes += 1

                cluster_info['notready_nodes'] = notready_nodes

                version = version_api.get_code()
                cluster_info['k8s_version'] = version.git_version

            except ApiException as e:
                cluster_info['error'] = f"API错误({e.status}): {e.reason}"
            except Exception as e:
                cluster_info['error'] = f"连接失败: {str(e)}"

            all_clusters_info[cluster_name] = cluster_info  # 仍以 cluster_name 作为键

        # return json.dumps(all_clusters_info, indent=4, ensure_ascii=False)
        return all_clusters_info
    except Exception as e:
        return json.dumps({
            'error': f"系统错误: {str(e)}"
        }, indent=4)


async def process_kubeconfigs():
    """
    检测当前目录下的 kubestage 文件夹中的 kubeconfig 格式文件,
    计算每个文件的大写 MD5 值,将其改名成对应的 MD5 值,
    并按照规则 [md5[0]/md5[1]/md5[2]/md5] 的层级形式存储到当前目录下的 savekubes 目录中。
    如果 MD5 冲突,则记录冲突文件信息并跳过该文件。
    记录每个集群kubeconfig在savekubes目录里的存储地址和其它信息到数据表
    """
    # 定义路径
    current_dir = Path.cwd()
    app_dir = current_dir / "app"
    source_dir = app_dir / "kubestage"
    target_dir = app_dir / "savekubes"
    db_path = app_dir / "mk8s.db"  # SQLite 数据库路径

    # 确保目标目录存在
    target_dir.mkdir(parents=True, exist_ok=True)

    # 连接 SQLite 数据库（自动创建文件）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mk8s (
            md5_hash TEXT PRIMARY KEY,
            server_url TEXT NOT NULL,
            now_path TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()

    # 记录已处理的 MD5 值
    md5_map = {}

    for file_path in source_dir.glob("*"):
        if not file_path.is_file():
            continue

        try:
            # 读取并解析 YAML
            with open(file_path, "rb") as f:
                file_content = f.read()
                config_data = yaml.safe_load(file_content)

            # 验证基础结构
            if not all(key in config_data for key in ["apiVersion", "clusters", "contexts"]):
                raise ValueError("缺少必要字段: apiVersion, clusters 或 contexts")

            if not isinstance(config_data["clusters"], list) or not isinstance(config_data["contexts"], list):
                raise ValueError("clusters 或 contexts 必须是列表类型")

            # 提取 server URL
            server_url = None
            for cluster in config_data["clusters"]:
                if "cluster" in cluster and "server" in cluster["cluster"]:
                    server_url = cluster["cluster"]["server"]
                    break
            if not server_url:
                raise ValueError("未找到有效的 server URL")

            # 计算 MD5
            md5_hash = hashlib.md5(file_content).hexdigest().upper()

            # 检查 MD5 冲突
            if md5_hash in md5_map:
                print(f"MD5 冲突: 文件 {file_path} 和 {md5_map[md5_hash]} 具有相同的 MD5 值 ({md5_hash}),跳过。")
                continue
 
            # 记录 MD5 映射
            md5_map[md5_hash] = str(file_path)

            # 构造目标路径并移动文件
            sub_dir = target_dir / md5_hash[0] / md5_hash[1] / md5_hash[2]
            target_file_path = sub_dir / md5_hash
            sub_dir.mkdir(parents=True, exist_ok=True)
            os.rename(file_path, target_file_path)
            # print(f"已处理: {file_path} -> {target_file_path}")
            print("集群新增成功! kubeconfig在: %s" % target_file_path)

            # 插入到 SQLite 数据库
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            print(md5_hash, server_url, target_file_path, file_path.name, timestamp)
            cursor.execute(
                "INSERT INTO mk8s (md5_hash, server_url, now_path, original_filename, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                (md5_hash, server_url, str(target_file_path), file_path.name, timestamp)
            )
            conn.commit()

        # except yaml.YAMLError as e:
        #     error_mark = getattr(e, "problem_mark", None)
        #     if error_mark:
        #         error_line = error_mark.line + 1
        #         error_column = error_mark.column + 1
        #         error_message = (
        #             f"YAML 格式错误：第{error_line}行,第{error_column}列：{e.problem}"
        #         )
        #     else:
        #         error_message = f"YAML 解析失败：{str(e)}"
        #     print(f"文件 {file_path} 不是有效的 kubeconfig 格式（{error_message}）,跳过。")

        # except ValueError as e:
        #     print(f"文件 {file_path} 不是有效的 kubeconfig 格式（{str(e)}）,跳过。")

        # except Exception as e:
        #     print(f"处理文件 {file_path} 时发生未知错误：{str(e)},跳过。")
        except:
            import traceback
            traceback.print_exc()

    cursor.execute("SELECT * FROM mk8s;")
    rows = cursor.fetchall()
    print(rows)
    
    # 关闭数据库连接
    conn.close()


if __name__ == "__main__":
    # get_multiple_cluster()
    # get_multiple_cluster()
    # ret = get_cluster_nodes_by_server("192_168_0_3-6443")   
    
    # print(ret)
    # process_kubeconfigs()
    pass
    