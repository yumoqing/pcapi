import time
import yaml
import traceback
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from appPublic.log import debug
from .k8s_utils_public import format_source_labels

def create_or_update_namespace(v1, namespace_name):
    """创建或更新命名空间"""
    try:
        v1.read_namespace(namespace_name)
        debug(f"namespace_name={namespace_name} 命名空间已存在,跳过创建。")
    except ApiException as e:
        if e.status == 404:
            body = {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": namespace_name}
            }
            v1.create_namespace(body=body)
            debug(f"namespace_name={namespace_name} 命名空间创建成功。")
        else:
            raise ValueError(f'{e}')

def create_or_update_service_account(v1, namespace_name, service_account_name):
    """创建或更新服务账户"""
    try:
        v1.read_namespaced_service_account(name=service_account_name, namespace=namespace_name)
        debug(f"namespace_name={namespace_name} service_account_name={service_account_name} 服务账户已存在,跳过创建。")
    except ApiException as e:
        if e.status == 404:
            body = {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "name": service_account_name,
                    "namespace": namespace_name
                }
            }
            v1.create_namespaced_service_account(namespace=namespace_name, body=body)
            debug(f"namespace_name={namespace_name} service_account_name={service_account_name} 服务账户创建成功。")
        else:
            raise ValueError(f'{e}')

def create_or_update_service(v1, namespace_name, service_name, port_mode, internal_port, selector,
                             inside_port, outside_port):
    """创建或更新服务"""
    try:
        existing_service = v1.read_namespaced_service(name=service_name, namespace=namespace_name)
        update_info = []
        need_update = False

        ports_config = [
            {
                "name": f"podport{internal_port}",
                "protocol": "TCP",
                "port": internal_port,
                "targetPort": inside_port,
                "nodePort": outside_port if port_mode == "NodePort" else None
            }
        ]

        if existing_service.spec.type != port_mode:
            need_update = True
            update_info.append(f"服务类型从 {existing_service.spec.type} 更新为 {port_mode}")
            existing_service.spec.type = port_mode

        if existing_service.spec.selector != selector:
            need_update = True
            update_info.append(f"服务选择器从 {existing_service.spec.selector} 更新为 {selector}")
            existing_service.spec.selector = selector

        if existing_service.spec.ports != ports_config:
            need_update = True
            update_info.append(f"服务端口配置更新")
            existing_service.spec.ports = ports_config

        if need_update:
            v1.patch_namespaced_service(name=service_name, namespace=namespace_name, body=existing_service)
            debug(f"service_name={service_name} update_info={update_info} 服务已更新,更新内容: {update_info}")
        else:
            debug(f"service_name={service_name} 服务配置无变化,无需更新。")
        return existing_service

    except ApiException as e:
        if e.status == 404:
            ports_config = [
                {
                    "name": f"podport{internal_port}",
                    "protocol": "TCP",
                    "port": internal_port,
                    "targetPort": inside_port,
                    "nodePort": outside_port if port_mode == "NodePort" else None
                }
            ]
            body = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {"name": service_name, "namespace": namespace_name},
                "spec": {"type": port_mode, "selector": selector, "ports": ports_config}
            }
            v1.create_namespaced_service(namespace=namespace_name, body=body)
            debug(f"service_name={service_name} 服务创建成功。")
            return v1.read_namespaced_service(name=service_name, namespace=namespace_name)
        else:
            raise ValueError(f'{e}')

# def create_persistent_volume(v1, namespace_name, pv_name, capacity, access_modes, storage_class_name, nfs_server, nfs_path):
#     """创建PV"""
#     try:
#         v1.read_persistent_volume(name=pv_name)
#         debug(f"PersistentVolume {pv_name} 已存在,跳过创建。")
#     except ApiException as e:
#         if e.status == 404:
#             body = {
#                 "apiVersion": "v1",
#                 "kind": "PersistentVolume",
#                 "metadata": {
#                     "name": pv_name,
#                     "namespace": namespace_name
#                     },
#                 "spec": {
#                     "capacity": {
#                         "storage": capacity
#                     },
#                     "accessModes": access_modes,
#                     "persistentVolumeReclaimPolicy": "Retain",
#                     "storageClassName": storage_class_name,
#                     "nfs": {
#                         "server": nfs_server,
#                         "path": nfs_path
#                     }
#                 }
#             }
#             try:
#                 v1.create_persistent_volume(body=body)
#                 debug(f"PersistentVolume {pv_name} 创建成功。")
#             except ApiException as create_e:
#                 raise Exception(f"创建 PersistentVolume {pv_name} 失败: {create_e.reason}")
#         else:
#             raise Exception(f"检查 PersistentVolume {pv_name} 是否存在时出错: {e.reason}")

def create_persistent_volume_claim(v1, namespace_name, pvc_name, access_modes, storage_class_name, pvc_capacity, source_selflabel):
    """创建pvc"""
    try:
        v1.read_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace_name)
        debug(f"PersistentVolumeClaim {pvc_name} 已存在,跳过创建。")
    except ApiException as e:
        if e.status == 404:
            body = {
                "apiVersion": "v1",
                "kind": "PersistentVolumeClaim",
                "metadata": {
                    "name": pvc_name,
                    "namespace": namespace_name,
                    "labels": source_selflabel
                },
                "spec": {
                    "accessModes": access_modes,
                    "resources": {"requests": {"storage": pvc_capacity}},
                    "storageClassName": storage_class_name
                }
            }
            try:
                v1.create_namespaced_persistent_volume_claim(namespace=namespace_name, body=body)
                debug(f"PersistentVolumeClaim {pvc_name} 创建成功。")
            except ApiException as create_e:
                raise Exception(f"创建 PersistentVolumeClaim {pvc_name} 失败: {create_e.reason}")
        else:
            raise Exception(f"检查 PersistentVolumeClaim {pvc_name} 是否存在时出错: {e.reason}")

def create_or_update_statefulset(apps_v1, v1, namespace_name, statefulset_name, service_account_name,
                                 image, replicas, cpu_limit, memory_limit, node_selector,
                                 container_name, initial_password, restart_policy,
                                 inside_port, volume_mount_path, pvc_name,
                                 env_vars, readiness_probe, liveness_probe, 
                                 source_selflabel, ephemeral_storage, source_gpu):
    """创建或更新StatefulSet,共享单个pvc"""
    try:
        existing_statefulset = apps_v1.read_namespaced_stateful_set(name=statefulset_name, namespace=namespace_name)
        update_info = []
        need_update = False
        template = existing_statefulset.spec.template
        container = template.spec.containers[0]
  
        # 更新副本数
        if existing_statefulset.spec.replicas != replicas:
            need_update = True
            update_info.append(f"副本数从 {existing_statefulset.spec.replicas} 更新为 {replicas}")
            existing_statefulset.spec.replicas = replicas

        # 更新服务账户和重启策略
        if template.spec.service_account_name != service_account_name:
            need_update = True
            update_info.append(f"服务账户从 {template.spec.service_account_name} 更新为 {service_account_name}")
            template.spec.service_account_name = service_account_name

        if template.spec.restart_policy != restart_policy:
            need_update = True
            update_info.append(f"重启策略从 {template.spec.restart_policy} 更新为 {restart_policy}")
            template.spec.restart_policy = restart_policy

        # 更新容器配置
        if container.name != container_name:
            need_update = True
            update_info.append(f"容器名称从 {container.name} 更新为 {container_name}")
            container.name = container_name

        if container.image != image:
            need_update = True
            update_info.append(f"镜像从 {container.image} 更新为 {image}")
            container.image = image

        if container.env != env_vars:
            need_update = True
            update_info.append(f"环境变量更新为 {env_vars}")
            container.env = env_vars

        update_limits_info = {
                        "cpu": cpu_limit, 
                        "memory": memory_limit,
                        "ephemeral-storage": ephemeral_storage,
                        "nvidia.com/gpu" : source_gpu
                    }
        if container.resources.limits != update_limits_info:
            need_update = True
            update_info.append(f"资源实例消费上限更新为 {update_limits_info}")
            container.resources.limits = update_limits_info

        #update_requests_info = {"ephemeral-storage": ephemeral_storage}
        # if container.resources.requests != update_limits_info:
        #     need_update = True
        #     update_info.append(f"资源实例消费上限更新为 {update_limits_info}")
            container.resources.requests = update_limits_info

        if container.ports != [{"containerPort": inside_port}]:
            need_update = True
            update_info.append(f"容器端口从 {container.ports} 更新为 {inside_port}")
            container.ports = [{"containerPort": inside_port}]

        # 更新探针
        if container.readiness_probe != readiness_probe:
            need_update = True
            update_info.append(f"就绪探针更新")
            container.readiness_probe = readiness_probe

        if container.liveness_probe != liveness_probe:
            need_update = True
            update_info.append(f"存活探针更新")
            container.liveness_probe = liveness_probe

        # 更新卷挂载
        if container.volume_mounts != [{"name": pvc_name, "mountPath": volume_mount_path}]:
            need_update = True
            update_info.append(f"卷挂载从 {container.volume_mounts} 更新为 {volume_mount_path}")
            container.volume_mounts = [{"name": pvc_name, "mountPath": volume_mount_path}]

        if need_update:
            apps_v1.patch_namespaced_stateful_set(name=statefulset_name, namespace=namespace_name, body=existing_statefulset)
            debug(f"StatefulSet {statefulset_name} 更新成功: {update_info}")
        else:
            debug(f"StatefulSet {statefulset_name} 配置无变化")
        return existing_statefulset

    except ApiException as e:
        traceback.print_exc()
        limits_requests = {
                        "cpu": cpu_limit,
                        "memory": memory_limit,
                        "ephemeral-storage": ephemeral_storage,
                        "nvidia.com/gpu" : source_gpu
                        }
        if e.status == 404:
            container_config = {
                "name": container_name,
                "image": image,
                "env": env_vars,
                "resources": {
                    "limits": limits_requests,
                    "requests": limits_requests
                    #{"ephemeral-storage": ephemeral_storage} # 容器启动时请求 10GB 临时存储
                    },
                "ports": [{"containerPort": inside_port}],
                "readinessProbe": readiness_probe,
                "livenessProbe": liveness_probe,
                "volumeMounts": [{"name": pvc_name, "mountPath": volume_mount_path}],
                "command": [
                    "/bin/bash",
                    "-c",
                    f"echo 'root:{initial_password}' | chpasswd && service ssh start && while true; do sleep 1; done"
                ]
            }
            body = {
                "apiVersion": "apps/v1",
                "kind": "StatefulSet",
                "metadata": {"name": statefulset_name, "namespace": namespace_name},
                "spec": {
                    "replicas": replicas,
                    "selector": {"matchLabels": source_selflabel},
                    "serviceName": statefulset_name,
                    "template": {
                        "metadata": {"labels": source_selflabel},
                        "spec": {
                            "runtimeClassName": "nvidia",  # 指定使用 nvidia runtime"
                            "serviceAccountName": service_account_name,
                            "restartPolicy": restart_policy,
                            "containers": [container_config],
                            "nodeSelector": node_selector,
                            # 基于客户端IP保持会话亲和性(可选):客户端请求始终到最开始pod；
                            # 但也有弊端，假若某个Pod宕机或环境异常，客户端还是会一直请求该Pod，导致无法访问。
                            # "sessionAffinity": "ClientIP",
                            "volumes": [{
                                "name": pvc_name,
                                "persistentVolumeClaim": {
                                    "claimName": pvc_name
                                }
                            }]
                        }
                    }
                }
            }
            apps_v1.create_namespaced_stateful_set(namespace=namespace_name, body=body)
            debug(f"StatefulSet {statefulset_name} 创建成功,副本数: {replicas}")
            return apps_v1.read_namespaced_stateful_set(name=statefulset_name, namespace=namespace_name)
        else:
            raise ValueError(f'{e}')

def delete_persistent_volume(v1, pv_name):
    """删除PV"""
    try:
        v1.delete_persistent_volume(name=pv_name)
        debug(f"PersistentVolume {pv_name} 删除成功")
    except ApiException as e:
        raise Exception(f"删除 PersistentVolume {pv_name} 失败: {e.reason}")

def delete_persistent_volume_claim(v1, namespace_name, pvc_name):
    """删除pvc"""
    try:
        v1.delete_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace_name)
        debug(f"PersistentVolumeClaim {pvc_name} 删除成功")
    except ApiException as e:
        raise Exception(f"删除 PersistentVolumeClaim {pvc_name} 失败: {e.reason}")

def delete_namespace(v1, namespace_name, root_namespace="default_namespace"):
    """删除命名空间"""
    if namespace_name != root_namespace:
        try:
            v1.delete_namespace(namespace_name, propagation_policy="Foreground")
            debug(f"命名空间 {namespace_name} 删除请求已提交")
        except ApiException as e:
            raise Exception(f"删除命名空间 {namespace_name} 失败: {e.reason}")
    else:
        debug(f"跳过删除根命名空间 {namespace_name}")

def delete_service_account(v1, namespace_name, service_account_name, root_namespace="default_namespace"):
    """删除服务账户"""
    if namespace_name != root_namespace:
        try:
            v1.delete_namespaced_service_account(service_account_name, namespace_name)
            debug(f"服务账户 {service_account_name} 删除成功")
        except ApiException as e:
            raise Exception(f"删除服务账户 {service_account_name} 失败: {e.reason}")
    else:
        debug(f"跳过删除根命名空间中的服务账户 {service_account_name}")

def delete_service(v1, namespace_name, service_name):
    """删除服务"""
    try:
        v1.delete_namespaced_service(service_name, namespace_name)
        debug(f"服务 {service_name} 删除成功")
    except ApiException as e:
        raise Exception(f"删除服务 {service_name} 失败: {e.reason}")

def delete_statefulset(apps_v1, namespace_name, statefulset_name):
    """删除StatefulSet"""
    try:
        apps_v1.delete_namespaced_stateful_set(
            name=statefulset_name,
            namespace=namespace_name,
            propagation_policy="Foreground"
        )
        debug(f"StatefulSet {statefulset_name} 删除请求已提交")
    except ApiException as e:
        raise Exception(f"删除 StatefulSet {statefulset_name} 失败: {e.reason}")

def handle_k8s_operations(frontend_params):
    """
        处理Kubernetes资源操作
    """
    # 参数验证
    required_params = [
        "action",
        "namespace_name",
        "serviceaccount_name",
        "service_name",
        "podcd_name",
        "pod_imagepath",
        "source_replicasetnum",
        "source_cpurate",
        "source_memrate",
        "source_portmode",
        "source_apiport",
        "source_insideport",
        "source_outsideport",
        "source_name",
        "source_authpasswd",
        "source_restartpolicy",
        "source_mountpath",
        "host",  # nfs_server
        "source_selflabel",
        # "source_nodeselector"
    ]
    for param in required_params:
        if not frontend_params.get(param):
            debug(f"param={param} 错误：缺少必要参数 {param}")
            raise ValueError(f"缺少必要参数: {param}")
        
    kubeconfig = yaml.safe_load(frontend_params.pop("kubeconfig"))
    config.load_kube_config_from_dict(kubeconfig)
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    action = frontend_params["action"]
    namespace_name = frontend_params["namespace_name"]
    service_account_name = frontend_params["serviceaccount_name"]
    service_name = frontend_params["service_name"]
    statefulset_name = frontend_params["podcd_name"]
    image = frontend_params["pod_imagepath"]
    replicas = int(frontend_params.get("source_replicasetnum"))
    cpu_limit = frontend_params["source_cpurate"]
    memory_limit = frontend_params["source_memrate"]
    port_mode = frontend_params["source_portmode"]
    internal_port = int(frontend_params["source_apiport"])
    inside_port = int(frontend_params["source_insideport"])
    outside_port = int(frontend_params["source_outsideport"])
    container_name = frontend_params["source_name"]
    initial_password = frontend_params["source_authpasswd"]
    restart_policy = frontend_params["source_restartpolicy"]
    volume_mount_path = frontend_params["source_mountpath"]
    pvc_name = container_name.replace(" ", "").lower() + "-pvc"
    env_varsa = [{"name": "ENV_VAR_NAME", "value": "ENV_VAR_VALUE"}]
    env_vars = frontend_params.get("env_vars", env_varsa)
    readiness_probea = {
            "exec": {
                "command": ["/bin/bash", "-c", "ls /"]
            },
            "initialDelaySeconds": 10,
            "periodSeconds": 5
        }
    readiness_probe = frontend_params.get("readiness_probe", readiness_probea)
    liveness_probea = {
            "exec": {
                "command": ["service", "ssh", "status"]
            },
            "initialDelaySeconds": 20,
            "periodSeconds": 10
        }
    liveness_probe = frontend_params.get("liveness_probe", liveness_probea)
    access_modesa = ["ReadWriteMany"] #NFS 存储类通常需要 ReadWriteOnce 或 ReadOnlyMany，否则可能导致调度失败。
    # access_modesa = ["ReadOnlyMany","ReadWriteOnce"]
    access_modes = frontend_params.get("access_modes",access_modesa)
    storage_class_name = frontend_params.get("storage_class_name", "nfs-storage-class")
    nfs_server = frontend_params.get("host")
    nfs_path = frontend_params.get("nfs_path","/d/k8s_nss")
    pv_name = f"{pvc_name}-pv"
    source_storagelimits = frontend_params.get("source_storagelimits", "50Gi")
    pv_capacity = frontend_params.get("pv_capacity", source_storagelimits)
    pvc_capacity = frontend_params.get("pvc_capacity",source_storagelimits)
    # 以下参数暂未开放-----------------------------------------------------------------------------------
    source_selflabel = format_source_labels(frontend_params.get("source_selflabel",":"),type="pod")
    node_selector = format_source_labels(frontend_params.get("source_nodeselector","="),type="node")
    # 限制容器最多使用 10GB 临时存储（包括根目录）
    ephemeral_storage = frontend_params.get("ephemeral_storage","10Gi") 
    # 限制Pod占用GPU数量，默认为0
    source_gpu = int(frontend_params.get("source_gpu", "0"))
    # ------------------------------------------------------------------------------------------------
    # 删除选项控制
    delete_options = {
        "pvc": frontend_params.get("delete_pvc", True),
        # "pv": frontend_params.get("delete_pv", True),
        "service": frontend_params.get("delete_service", True),
        "service_account": frontend_params.get("delete_service_account", False),
        "namespace": frontend_params.get("delete_namespace", False)
    }
    if action == "apply":
        # 创建资源（按依赖顺序）
        create_or_update_namespace(v1, namespace_name)
        create_or_update_service_account(v1, namespace_name, service_account_name)
        create_or_update_service(v1, namespace_name, service_name, port_mode, internal_port, source_selflabel, inside_port, outside_port)
        # create_persistent_volume(v1, namespace_name, pv_name, pv_capacity, access_modes, storage_class_name, nfs_server, nfs_path)
        create_persistent_volume_claim(v1, namespace_name, pvc_name, access_modes, storage_class_name, pvc_capacity, source_selflabel)
        create_or_update_statefulset(
            apps_v1, v1, namespace_name, statefulset_name, service_account_name,
            image, replicas, cpu_limit, memory_limit, node_selector,
            container_name, initial_password, restart_policy,
            inside_port, volume_mount_path, pvc_name,
            env_vars, readiness_probe, liveness_probe, source_selflabel, ephemeral_storage, source_gpu
        )
        debug(f"成功申请 {replicas} 个副本的 {statefulset_name},共享pvc: {pvc_name}")

    elif action == "delete":
        # 删除资源（按逆序）
        delete_statefulset(apps_v1, namespace_name, statefulset_name)

        # 等待一段时间,确保Pod完全终止
        debug(f'正在销毁资源实例,请稍等...')
        time.sleep(3)  # 可根据实际情况调整）
        
        if delete_options["pvc"]:
            delete_persistent_volume_claim(v1, namespace_name, pvc_name)
            
        # if delete_options["pv"]:
        #     delete_persistent_volume(v1, pv_name)
            
        if delete_options["service"]:
            delete_service(v1, namespace_name, service_name)
            
        if delete_options["service_account"]:
            delete_service_account(v1, namespace_name, service_account_name)
            
        if delete_options["namespace"]:
            delete_namespace(v1, namespace_name)
            
        debug(f"成功销毁 {statefulset_name} 及其相关资源")
    else:
        raise ValueError("action参数必须为'apply'或'delete'")

if __name__ == "__main__":
    # Service 端口（port）：客户端访问 Service 的端口（例如 2222）。
    # Pod 端口（targetPort）：后端 Pod 实际监听的端口（例如 22）。
    # NodePort（nodePort）：集群外访问的端口（例如 30060）。
    kbc = "apiVersion: v1\nclusters:\n- cluster:\n    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJBZ0lJTGd4THlGMjM3QmN3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TlRBME1ETXdOelE1TXpWYUZ3MHpOVEEwTURFd056VTBNelZhTUJVeApFekFSQmdOVkJBTVRDbXQxWW1WeWJtVjBaWE13Z2dFaU1BMEdDU3FHU0liM0RRRUJBUVVBQTRJQkR3QXdnZ0VLCkFvSUJBUURQUm5hdkZmNXBTWWUvVmJLc0s2SnhEazhyc2hsc2h5WnNNRk8xZDVhZG45Z055T0wwR2NtbEsrQ1EKVklKSnF3RklJeSsxUVlEd3VRMytzczEwYmV2Y2lqM1BRanluaXJRRkNhRlA0NHh2ZkEyK2thV1FYeTVncGwrMwpjSkI1K1MxVmx2Vi9aSHQ5SXgwNjFCdHB4dE5oMUkxNS9IYk4rWmVNNnEvd3lxUW93Y01ub2pyNDltYkxxOWNwCnFSem5LL2FwWXlBYnljUk9uWWlIZ0FjQWdsclFOTjBKUEJZd2dRd0pIUmlIcGhtVFBkdmY2ckxkNFR0dFl2OXgKdmZIRDNjVUdwZkVBUElaNUJBVi9ZM3p5V0pSbDQzSFV2Ri9jemNDQ01jOVlUd3VXaEpxb2doUUZUdnNuSVZzTwovNEtKQzRwQXFSenJlZFRWdExmMXgzQlRpVCt0QWdNQkFBR2pXVEJYTUE0R0ExVWREd0VCL3dRRUF3SUNwREFQCkJnTlZIUk1CQWY4RUJUQURBUUgvTUIwR0ExVWREZ1FXQkJUZjRZbzBpOVpIZC9ObzdkYWZrZVRTbzVzdzN6QVYKQmdOVkhSRUVEakFNZ2dwcmRXSmxjbTVsZEdWek1BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRRERLalJWVVp1YwppckJ4QWdZWnBBeW5NSHdWQTF6YStVT09FM1U0MEMyVTN0VGgrK1BsN2o2ZGJZTWNWdEFvTXhxaDRiVjNQRW5SCmtWcWNaN2NjS3FGSXduZlhHK0ZGTVVwazVoTk0xLzc2UXBobi9OWk8zSStSVjFtV0VOU1BzM1FZdEVoWktXUlgKYWRXZ0krK0x1cUZyZVpTVzVjRXNnMWZDODFtd3dhTXdkRHZWcFJZMFEwWlBsMGFqTURsSlNDaDNOSXpQOS82bwpndXBrY1JSdWtvRGlscWVraXlrRWJ5OVJCWHZIbXo3Q0sxQ1ZnZXZJTDZrVnRPRFF2Rm10Qm1WemlRNWFDcXJOCmtZNmd6OUNGMkdKc2M4UkZrcWQxbzdMelhPakJsTkdzN2k2WmdEOE1Ca2tiank2RmZDZWVndmxOOGFCU2VmblEKZ2ZNOVptbnRpMVNDCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K\n    server: https://192.168.0.3:6443\n  name: kubernetes\ncontexts:\n- context:\n    cluster: kubernetes\n    user: kubernetes-admin\n  name: kubernetes-admin@kubernetes\ncurrent-context: kubernetes-admin@kubernetes\nkind: Config\npreferences: {}\nusers:\n- name: kubernetes-admin\n  user:\n    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURJRENDQWdpZ0F3SUJBZ0lIVGZPdmU4TzBJVEFOQmdrcWhraUc5dzBCQVFzRkFEQVZNUk13RVFZRFZRUUQKRXdwcmRXSmxjbTVsZEdWek1CNFhEVEkxTURRd016QTNORGt6TlZvWERUSTJNRFF3TXpBM05UUXpOMW93TkRFWApNQlVHQTFVRUNoTU9jM2x6ZEdWdE9tMWhjM1JsY25NeEdUQVhCZ05WQkFNVEVHdDFZbVZ5Ym1WMFpYTXRZV1J0CmFXNHdnZ0VpTUEwR0NTcUdTSWIzRFFFQkFRVUFBNElCRHdBd2dnRUtBb0lCQVFEWVJJT3h0TWFkOWs2T1JsL1UKZ2ZnZVJDQkpjZmMrc2ZFbzkxeW4vc05KZFVIbWRuamtMaC9wRjcwZkdoVWZ3R2t5dzR0WkdpTFFNR0xwclpyeAphVTdJT0R3a3I2ejl1SkQzaHlFZExhZGpZT0NOMHJhUFNpV05GV1QwSVN2UVBjZzNGQkQ2YmFHb2RtSmN5YnBPCk5qY1VZZmh5WEVqRXMwOU92QzhhZUJCbm9Na1RkRk53dlFaYXE2LzR3eTUyN0k3aUdIUVdvL21JS1VUVHhzRFgKMzJnVXErZmRVMEh5STJJeWhNMGdwT29uNURCVmRUbWsyMkZsVHk0ZWJ3Q3R4QmMvRCtpelhuZFpVd2tHMExMVwpqTEc4L3JkWTZ4WFJDVkhHM1BWNURRK0JvNEpnMTUwWWFSUnBKeDJYSGxad3N5OFBZcWVLcTM0b1pxczRTRndmCjJCY3JBZ01CQUFHalZqQlVNQTRHQTFVZER3RUIvd1FFQXdJRm9EQVRCZ05WSFNVRUREQUtCZ2dyQmdFRkJRY0QKQWpBTUJnTlZIUk1CQWY4RUFqQUFNQjhHQTFVZEl3UVlNQmFBRk4vaGlqU0wxa2QzODJqdDFwK1I1TktqbXpEZgpNQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUJBUUFTR0phc1EyQXpLdVNZWFdtMGlYOUhnWTNZQUJGMHpYRzRKZU5lCjREekxkOHF2TXlqRGMwUWFWSUtNbWswemhrV1ZIQzNKSEZWalRXcDBUNFE0TlVBMk8rOXFob1p0a25NL3dsQlUKS0Zab3ZHNFd6SU1sdVJwL21ZRUIzL3dHbkFPV01MdEtBSWJ3d3FRVWl4VW5KYkxCeG4xQ1k5ZERzb1o4VmZZMQp4N2R0WDBJWjJkbU1ETTVLV1lrbW5tQWJBR0tXazZBR3pVWEpWNmlTU3laYjlWLzNuN3hmZlpZRkVDQXBQNk91CjhmRGdIVjBCdEMxS3VmU0tsTitLMnF2aXAzMlRjRHdoTEVHQWQ2aU9qYzhBRXlHelJmOWY4M0xUSGJ2dGtibjYKR0VQQlBQSExSTFlQWEh0OE9LbHdNOThwQWxkSkIyWEJ6UEttc0JFeGFOSWRXd2FTCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K\n    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBMkVTRHNiVEduZlpPamtaZjFJSDRIa1FnU1hIM1BySHhLUGRjcC83RFNYVkI1blo0CjVDNGY2UmU5SHhvVkg4QnBNc09MV1JvaTBEQmk2YTJhOFdsT3lEZzhKSytzL2JpUTk0Y2hIUzJuWTJEZ2pkSzIKajBvbGpSVms5Q0VyMEQzSU54UVErbTJocUhaaVhNbTZUalkzRkdINGNseEl4TE5QVHJ3dkduZ1FaNkRKRTNSVApjTDBHV3F1ditNTXVkdXlPNGhoMEZxUDVpQ2xFMDhiQTE5OW9GS3ZuM1ZOQjhpTmlNb1ROSUtUcUorUXdWWFU1CnBOdGhaVTh1SG04QXJjUVhQdy9vczE1M1dWTUpCdEN5MW95eHZQNjNXT3NWMFFsUnh0ejFlUTBQZ2FPQ1lOZWQKR0drVWFTY2RseDVXY0xNdkQyS25pcXQrS0dhck9FaGNIOWdYS3dJREFRQUJBb0lCQVFDQ1djRjZ3YmdaQzVWTApvZFV1MCt1RjZvLy9WS2F1YmpncDlmWXQ5NXNqVW42Vzl2OWtvUHh3MVBNVHBQZm9mR09yeWpyYVNLdUZDalVFCkhiUlBINmJ4ZlJ1YkRSdmFqWDByQkpLTDhMRjhiNjdKTEtFR2VxMXBmT1N0VkxVQXZjeElqbHF4WnBUU1loQmwKVnQxcE9MbzRHZGpTclJiYklDeUVDMTdrdUV0QytZV3lFb3E5MmlLNVdMTHdHM2hwVzhyVlVLVzZ2T0cyd0l4bAp0RWhMSGpOOWtnb1VVa2pORG9tK2FlcVVxeXhDeUZEdll4UmdhVTd0Y3pJSk52SUk3aDYxaExQbEZtMmxGQ0xlCjhjeTdKUDMyV1ZDSUpUMHhRNkJJRTdvVld4WWIvMzFVSHYrTHg0UHlBcFpiZ3piMjlvQm54VjhneUxnVjZDWW0Kd1psQlQ4S2hBb0dCQU9tMFZqTkVHVm5EaXNsTDFVVkNKYzFCVU1KcjNwalQvV0g4d2s0UzJYWmhwRWdVQmpQYgpDM3Y5czkxNHh6SjhXYWFtUFZPVGZMRmxzRWFLNnJpMFhjQkhXQi9ob1R1aDVKaDByS1RNWWFMTm9SdU00VCt6Ci9zUG1aY1ZMVXcxdHFmd3U5YlVpSTJCQURQNFM2MUFubk5hSnF1UmFWRk8vT1pqZUkvbHJzMVBSQW9HQkFPem0KVTNvcjNuSDh4WHI2WDNJUjRDM3l3TkZLaHNVVE44VmdWNWRVL0U5RmRHTldUVzRkWHdCK01jeUlQMlFLbjlycwpmcU9Cb0c3NlRKVHF0YzVobjY5Q014c1lVNVdPcDhOZW9oaXplY1luSTFjTk94TmZwdzZDdUZVb1pmTFFxU1dICmJ4dEVEaFkrcXJjR2FLZ3VzMk1uMkJ2cEg1bUhCTk5DL05pSVZ1WTdBb0dBZFlnVEhkOHVuSjBockJCdUpsR1kKN3p2YzRKb2RMV0RYZWpNQ2lQOGp6RXhZc1VNWXgzVnV0aUdtRmtpS2JWSnFSOHdzNVY0MEJJY3VlcHVjWmQyWApsSDZNekNQTjBVNmV4eWxPTmVidlowL2dxUmxWb3BMa0dpTkJwVkkzWjNaeVdYaElhNXJLamJwSWpuSjNVeTFJCnpBQWFLSk5nKzJrZEQwc1FibnlDaURFQ2dZQVFDZVA2OEg5bDdqd2NnRmozNnhmblpIa0RjbTAvYUhhdEtVR2sKNEQ4WXl0WC9aN2RrVGg3QmRNbkFWRFVlZTgyb3o3d2ZLOGFGM1BKVVhyT2lYbCttU1BBVzFJWE1LVlZZVjg3WApwMGNHVUY0SEpjRXJKWjIwME1yVUVTRWQyRnlyU3NrTjZvU2RvdTZCNTdBc09zVXdZR0UwT290R0pLc0I5cFlSCnZ1RkxRd0tCZ1FEZVFuRElPaUQ2SEpmc2loTC8xZ3dnS0hVeVc2WGYrNFhQODd3ZlVXT1N0SEpza29oTkZHdk8KSnpNdUFvc2V2UGFWdElCSXBZbFgycUlaaHlhdyt2VW9BUTZYRnR3WjM1QWo1T1VPbVFQQUJWbkVXZUJZRzdSaQpaZmhEU2NTek5xb3ozWFpjMnA4a2VMWE1XOWJsTDNNOTdOMFRLbExuZ0NrSTdoaXJMVGE2T0E9PQotLS0tLUVORCBSU0EgUFJJVkFURSBLRVktLS0tLQo="
    action = 'delete'  # 'apply' or 'delete' 删除的关键在于pod引擎名字
    frontend_params = {
        "kubeconfig": kbc,
        "cluster_type": "",
        "host": "192.168.0.3",
        "port": 22,
        "user": "root",
        "password": "Yuanshenhong.1",
        "action": action,
        "namespace_name": "4hbm8atruisou2bs24t-n-0",
        "serviceaccount_name": "4hbm8atruisou2bs24t-n-0-serviceaccount",
        "podcd_name": "dkxuui1mvir6sf-uzf-ut-statefulset",
        "service_name": "dkxuui1mvir6sf-uzf-ut-service",
        "instance_type": "LinuxOS",
        "clusterid": "4hBm8atruISOU2bs24t_N",
        "source_name": "kyy-ubuntu",
        "source_authuser": "root",
        "source_authpasswd": "kyycloud",
        "source_podengine": "StatefulSet",
        "source_replicasetnum": "1",
        "pod_imagepath": "docker.io/library/ubuntu:22.04",
        "source_memrate": "512Mi",
        "source_cpurate": "300m",
        "source_selflabel": "app:ubuntu",
        "source_portmode": "NodePort",
        "source_restartpolicy": "Always",
        "source_apiport": "2222",
        "source_insideport": "22",
        "source_outsideport": "30060",
        "source_mountpath": "/mnt/data",
        "source_storagelimits": "100Gi",
        "source_nodeselector": "kyy-gpu: true",
        "source_gpu": "1",  # 请求1个GPU
    }
    handle_k8s_operations(frontend_params)
