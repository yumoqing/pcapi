from ahserver.serverenv import ServerEnv
from ahserver.webapp import webapp
from ahserver.auth_api import get_client_ip
from ahserver.auth_api import AuthAPI
from appPublic.argsConvert import ArgsConvert
from appPublic.jsonConfig import getConfig
from appPublic.log import debug
from appPublic.worker import awaitify
from aiohttp import BasicAuth

from storage.common import get_storage_json	#示例
# from ldap.ldapOperate import *	#目前没有ldap服务器

# k8s多集群管理核心接口
from k8sManager.multiple_clusters import *

async def checkuserpasswd(obj, request, user, passwd):
	auth = request.headers.get('Authorization')
	if auth is None:
		debug(f'auth is None, {request.headers=}')
		return False
	if auth.startswith('Basic '):
		auther = BasicAuth('x')
		m = auther.decode(auth)
		username = m.login
		password = m.password
		config = getConfig()
		if username != config.authentication.user:
			debug(f'{username=},{password=}, user not match')
			return False
		if password != config.authentication.password:
			debug(f'{username=},{password=}, password not match')
			return False
		ip = get_client_ip(None, request)
		if ip not in config.authentication.iplist:
			debug(f'{username=},{password=}, ip not in allowed ip pools')
			return False
		return True
	debug(f'not a basic authentication')
	return False

async def create_namespaced_job_v1(namespace, jobdesc):
	batch_v1 = client.BatchV1Api()
	f = awaitify(batch_v1.create_namespaced_job)
	return await f(namespace=namespace, body=jobdesc)

async def determine_accommodat_by_kubeconfig_v1(params):
	f = awaitify(determine_accommodat_by_kubeconfig)
	return await f(params)

def paramify(data, ns):
	ac = ArgsConvert('${', '}$')
	d = ac.convert(data, ns)
	return d

def init_func():
	AuthAPI.checkUserPermission = checkuserpasswd
	g = ServerEnv()	
	# 示例代码
	g.create_namespaced_job_v1 = create_namespaced_job_v1
	g.paramify = paramify
	g.debug = debug

	###ldap相关
	# g.add_ldap_user=add_ldap_user
	# g.get_all_ldap_user=get_all_ldap_user
	# g.get_all_ldap_cn=get_all_ldap_cn
	# g.get_one_cn=get_one_cn
	# g.modify_password=modify_password
	# g.delete_ldap_user=delete_ldap_user

	### k8s多集群相关
	g.new_cluster_install = new_cluster_install
	g.get_multiple_cluster = get_multiple_cluster
	g.get_multiple_cluster_pod = get_multiple_cluster_pod
	g.get_cluster_nodes_by_server = get_cluster_nodes_by_server
	g.get_cluster_pods_by_server = get_cluster_pods_by_server
	g.delete_cluster_node = delete_cluster_node
	g.node_state_switch = node_state_switch
	g.yaml_apply_delete = yaml_apply_delete
	g.get_cluster_nodes_by_kubeconfig = get_cluster_nodes_by_kubeconfig
	g.determine_accommodat_by_kubeconfig = determine_accommodat_by_kubeconfig
	g.get_cluster_pods_by_kubeconfig = get_cluster_pods_by_kubeconfig
	g.node_label_opt = node_label_opt

	g.get_storage_json=get_storage_json
	g.result_dict={
		"status":False,
		"info":"operate failed",
		"data":{}
	}

if __name__ == '__main__':
	webapp(init_func)
