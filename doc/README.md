## pcapi_kboss.html和此文档内容是一样的,不要纠结看哪个,呈现形式不一样而已~


# pcapi_kboss容器云/算力中心服务核心API

## POST 集群节点绑定/解绑标签

POST /pcapi/api/v1/cluster/common/node_label_opt

给某算力中心的某集群中的某节点打标签

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|host|query|string| 是 |none|
|port|query|boolean| 是 |none|
|user|query|string| 是 |none|
|psssword|query|string| 是 |none|
|worker_node|query|string| 是 |目标节点|
|label|query|string| 是 |目标标签|
|opt|query|string| 是 |标签操作，label：绑定，unlabel：解绑|
|Authorization|header|string| 是 |base64加密ssh账号密码信息（示例是ysh,Kyy@123456）|

#### 详细说明

**Authorization**: base64加密ssh账号密码信息（示例是ysh,Kyy@123456）
用于pcapi服务校验客户端，下面是python写法
headers = basic_auth_headers('ssh账号', 'ssh密码')

> 返回示例

```json
{
  "status": true,
  "info": "节点绑定标签成功",
  "data": {}
}
```

```json
{
  "status": false,
  "info": "switch node failed",
  "data": {
    "state": "uncordon",
    "drain": false
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» info|string|true|none||none|
|» data|object|true|none||none|
|»» node_name|string|true|none||none|
|»» force|boolean|true|none||none|

## GET 集群节点库存检测接口

GET /pcapi/api/v1/cluster/common/determine_accommodat

接收平台传来的若干产品组合JSON和集群上下文信息
用于判断某集群中是否至少有一个可用节点来承载这个资源实例的创建

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|kubeconfig|query|string| 是 |集群上下文信息|
|resources|query|string| 是 |平台请求资源详情|
|Authorization|header|string| 是 |base64加密ssh账号密码信息（示例是ysh,Kyy@123456）|

#### 详细说明

**Authorization**: base64加密ssh账号密码信息（示例是ysh,Kyy@123456）
用于pcapi服务校验客户端，下面是python写法
headers = basic_auth_headers('ssh账号', 'ssh密码')

> 返回示例

> 200 Response

```json
[
  "置灰产品id_2",
  "置灰产品id_3",
  "置灰产品id_4"
]
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 创建k8s集群(master)

POST /pcapi/api/v1/cluster/common/new_cluster

通过ssh远程调度安装kubernetes集群的控制节点，
返回集群节点加入凭证及kubeconfig文件，
供工作节点注册加入和后续API管理Kubernetes资源

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cluster_type|query|string| 否 |集群类型,目前默认(只)支持kubernetes|
|host|query|string| 是 |安装控制节点的IP|
|port|query|integer| 是 |安装控制节点ssh端口|
|user|query|string| 是 |远程ssh认证用户|
|psssword|query|string| 是 |远程ssh认证密码|
|role|query|string| 是 |集控制节点角色|
|Authorization|header|string| 是 |base64加密ssh账号密码信息（示例是ysh,Kyy@123456）|

#### 详细说明

**Authorization**: base64加密ssh账号密码信息（示例是ysh,Kyy@123456）
用于pcapi服务校验客户端，下面是python写法
headers = basic_auth_headers('ssh账号', 'ssh密码')

> 返回示例

```json
{
  "status": true,
  "info": "operate success",
  "data": "kubeadm join 192.168.0.3:6443 --token nt80u6.gzpj9dxsrw79270c --discovery-token-ca-cert-hash sha256:7b33439b2a1b37a8d8938513bd45405f57c3255771c3b9b9b90af448d886b0c2 \n apiVersion: v1 clusters: - cluster: certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJBZ0lJTGd4THlGMjM3QmN3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TlRBME1ETXdOelE1TXpWYUZ3MHpOVEEwTURFd056VTBNelZhTUJVeApFekFSQmdOVkJBTVRDbXQxWW1WeWJtVjBaWE13Z2dFaU1BMEdDU3FHU0liM0RRRUJBUVVBQTRJQkR3QXdnZ0VLCkFvSUJBUURQUm5hdkZmNXBTWWUvVmJLc0s2SnhEazhyc2hsc2h5WnNNRk8xZDVhZG45Z055T0wwR2NtbEsrQ1EKVklKSnF3RklJeSsxUVlEd3VRMytzczEwYmV2Y2lqM1BRanluaXJRRkNhRlA0NHh2ZkEyK2thV1FYeTVncGwrMwpjSkI1K1MxVmx2Vi9aSHQ5SXgwNjFCdHB4dE5oMUkxNS9IYk4rWmVNNnEvd3lxUW93Y01ub2pyNDltYkxxOWNwCnFSem5LL2FwWXlBYnljUk9uWWlIZ0FjQWdsclFOTjBKUEJZd2dRd0pIUmlIcGhtVFBkdmY2ckxkNFR0dFl2OXgKdmZIRDNjVUdwZkVBUElaNUJBVi9ZM3p5V0pSbDQzSFV2Ri9jemNDQ01jOVlUd3VXaEpxb2doUUZUdnNuSVZzTwovNEtKQzRwQXFSenJlZFRWdExmMXgzQlRpVCt0QWdNQkFBR2pXVEJYTUE0R0ExVWREd0VCL3dRRUF3SUNwREFQCkJnTlZIUk1CQWY4RUJUQURBUUgvTUIwR0ExVWREZ1FXQkJUZjRZbzBpOVpIZC9ObzdkYWZrZVRTbzVzdzN6QVYKQmdOVkhSRUVEakFNZ2dwcmRXSmxjbTVsZEdWek1BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRRERLalJWVVp1YwppckJ4QWdZWnBBeW5NSHdWQTF6YStVT09FM1U0MEMyVTN0VGgrK1BsN2o2ZGJZTWNWdEFvTXhxaDRiVjNQRW5SCmtWcWNaN2NjS3FGSXduZlhHK0ZGTVVwazVoTk0xLzc2UXBobi9OWk8zSStSVjFtV0VOU1BzM1FZdEVoWktXUlgKYWRXZ0krK0x1cUZyZVpTVzVjRXNnMWZDODFtd3dhTXdkRHZWcFJZMFEwWlBsMGFqTURsSlNDaDNOSXpQOS82bwpndXBrY1JSdWtvRGlscWVraXlrRWJ5OVJCWHZIbXo3Q0sxQ1ZnZXZJTDZrVnRPRFF2Rm10Qm1WemlRNWFDcXJOCmtZNmd6OUNGMkdKc2M4UkZrcWQxbzdMelhPakJsTkdzN2k2WmdEOE1Ca2tiank2RmZDZWVndmxOOGFCU2VmblEKZ2ZNOVptbnRpMVNDCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K server: https://192.168.0.3:6443 name: kubernetes contexts: - context: cluster: kubernetes user: kubernetes-admin name: kubernetes-admin@kubernetes current-context: kubernetes-admin@kubernetes kind: Config preferences: {} users: - name: kubernetes-admin user: client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURJRENDQWdpZ0F3SUJBZ0lIVGZPdmU4TzBJVEFOQmdrcWhraUc5dzBCQVFzRkFEQVZNUk13RVFZRFZRUUQKRXdwcmRXSmxjbTVsZEdWek1CNFhEVEkxTURRd016QTNORGt6TlZvWERUSTJNRFF3TXpBM05UUXpOMW93TkRFWApNQlVHQTFVRUNoTU9jM2x6ZEdWdE9tMWhjM1JsY25NeEdUQVhCZ05WQkFNVEVHdDFZbVZ5Ym1WMFpYTXRZV1J0CmFXNHdnZ0VpTUEwR0NTcUdTSWIzRFFFQkFRVUFBNElCRHdBd2dnRUtBb0lCQVFEWVJJT3h0TWFkOWs2T1JsL1UKZ2ZnZVJDQkpjZmMrc2ZFbzkxeW4vc05KZFVIbWRuamtMaC9wRjcwZkdoVWZ3R2t5dzR0WkdpTFFNR0xwclpyeAphVTdJT0R3a3I2ejl1SkQzaHlFZExhZGpZT0NOMHJhUFNpV05GV1QwSVN2UVBjZzNGQkQ2YmFHb2RtSmN5YnBPCk5qY1VZZmh5WEVqRXMwOU92QzhhZUJCbm9Na1RkRk53dlFaYXE2LzR3eTUyN0k3aUdIUVdvL21JS1VUVHhzRFgKMzJnVXErZmRVMEh5STJJeWhNMGdwT29uNURCVmRUbWsyMkZsVHk0ZWJ3Q3R4QmMvRCtpelhuZFpVd2tHMExMVwpqTEc4L3JkWTZ4WFJDVkhHM1BWNURRK0JvNEpnMTUwWWFSUnBKeDJYSGxad3N5OFBZcWVLcTM0b1pxczRTRndmCjJCY3JBZ01CQUFHalZqQlVNQTRHQTFVZER3RUIvd1FFQXdJRm9EQVRCZ05WSFNVRUREQUtCZ2dyQmdFRkJRY0QKQWpBTUJnTlZIUk1CQWY4RUFqQUFNQjhHQTFVZEl3UVlNQmFBRk4vaGlqU0wxa2QzODJqdDFwK1I1TktqbXpEZgpNQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUJBUUFTR0phc1EyQXpLdVNZWFdtMGlYOUhnWTNZQUJGMHpYRzRKZU5lCjREekxkOHF2TXlqRGMwUWFWSUtNbWswemhrV1ZIQzNKSEZWalRXcDBUNFE0TlVBMk8rOXFob1p0a25NL3dsQlUKS0Zab3ZHNFd6SU1sdVJwL21ZRUIzL3dHbkFPV01MdEtBSWJ3d3FRVWl4VW5KYkxCeG4xQ1k5ZERzb1o4VmZZMQp4N2R0WDBJWjJkbU1ETTVLV1lrbW5tQWJBR0tXazZBR3pVWEpWNmlTU3laYjlWLzNuN3hmZlpZRkVDQXBQNk91CjhmRGdIVjBCdEMxS3VmU0tsTitLMnF2aXAzMlRjRHdoTEVHQWQ2aU9qYzhBRXlHelJmOWY4M0xUSGJ2dGtibjYKR0VQQlBQSExSTFlQWEh0OE9LbHdNOThwQWxkSkIyWEJ6UEttc0JFeGFOSWRXd2FTCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBMkVTRHNiVEduZlpPamtaZjFJSDRIa1FnU1hIM1BySHhLUGRjcC83RFNYVkI1blo0CjVDNGY2UmU5SHhvVkg4QnBNc09MV1JvaTBEQmk2YTJhOFdsT3lEZzhKSytzL2JpUTk0Y2hIUzJuWTJEZ2pkSzIKajBvbGpSVms5Q0VyMEQzSU54UVErbTJocUhaaVhNbTZUalkzRkdINGNseEl4TE5QVHJ3dkduZ1FaNkRKRTNSVApjTDBHV3F1ditNTXVkdXlPNGhoMEZxUDVpQ2xFMDhiQTE5OW9GS3ZuM1ZOQjhpTmlNb1ROSUtUcUorUXdWWFU1CnBOdGhaVTh1SG04QXJjUVhQdy9vczE1M1dWTUpCdEN5MW95eHZQNjNXT3NWMFFsUnh0ejFlUTBQZ2FPQ1lOZWQKR0drVWFTY2RseDVXY0xNdkQyS25pcXQrS0dhck9FaGNIOWdYS3dJREFRQUJBb0lCQVFDQ1djRjZ3YmdaQzVWTApvZFV1MCt1RjZvLy9WS2F1YmpncDlmWXQ5NXNqVW42Vzl2OWtvUHh3MVBNVHBQZm9mR09yeWpyYVNLdUZDalVFCkhiUlBINmJ4ZlJ1YkRSdmFqWDByQkpLTDhMRjhiNjdKTEtFR2VxMXBmT1N0VkxVQXZjeElqbHF4WnBUU1loQmwKVnQxcE9MbzRHZGpTclJiYklDeUVDMTdrdUV0QytZV3lFb3E5MmlLNVdMTHdHM2hwVzhyVlVLVzZ2T0cyd0l4bAp0RWhMSGpOOWtnb1VVa2pORG9tK2FlcVVxeXhDeUZEdll4UmdhVTd0Y3pJSk52SUk3aDYxaExQbEZtMmxGQ0xlCjhjeTdKUDMyV1ZDSUpUMHhRNkJJRTdvVld4WWIvMzFVSHYrTHg0UHlBcFpiZ3piMjlvQm54VjhneUxnVjZDWW0Kd1psQlQ4S2hBb0dCQU9tMFZqTkVHVm5EaXNsTDFVVkNKYzFCVU1KcjNwalQvV0g4d2s0UzJYWmhwRWdVQmpQYgpDM3Y5czkxNHh6SjhXYWFtUFZPVGZMRmxzRWFLNnJpMFhjQkhXQi9ob1R1aDVKaDByS1RNWWFMTm9SdU00VCt6Ci9zUG1aY1ZMVXcxdHFmd3U5YlVpSTJCQURQNFM2MUFubk5hSnF1UmFWRk8vT1pqZUkvbHJzMVBSQW9HQkFPem0KVTNvcjNuSDh4WHI2WDNJUjRDM3l3TkZLaHNVVE44VmdWNWRVL0U5RmRHTldUVzRkWHdCK01jeUlQMlFLbjlycwpmcU9Cb0c3NlRKVHF0YzVobjY5Q014c1lVNVdPcDhOZW9oaXplY1luSTFjTk94TmZwdzZDdUZVb1pmTFFxU1dICmJ4dEVEaFkrcXJjR2FLZ3VzMk1uMkJ2cEg1bUhCTk5DL05pSVZ1WTdBb0dBZFlnVEhkOHVuSjBockJCdUpsR1kKN3p2YzRKb2RMV0RYZWpNQ2lQOGp6RXhZc1VNWXgzVnV0aUdtRmtpS2JWSnFSOHdzNVY0MEJJY3VlcHVjWmQyWApsSDZNekNQTjBVNmV4eWxPTmVidlowL2dxUmxWb3BMa0dpTkJwVkkzWjNaeVdYaElhNXJLamJwSWpuSjNVeTFJCnpBQWFLSk5nKzJrZEQwc1FibnlDaURFQ2dZQVFDZVA2OEg5bDdqd2NnRmozNnhmblpIa0RjbTAvYUhhdEtVR2sKNEQ4WXl0WC9aN2RrVGg3QmRNbkFWRFVlZTgyb3o3d2ZLOGFGM1BKVVhyT2lYbCttU1BBVzFJWE1LVlZZVjg3WApwMGNHVUY0SEpjRXJKWjIwME1yVUVTRWQyRnlyU3NrTjZvU2RvdTZCNTdBc09zVXdZR0UwT290R0pLc0I5cFlSCnZ1RkxRd0tCZ1FEZVFuRElPaUQ2SEpmc2loTC8xZ3dnS0hVeVc2WGYrNFhQODd3ZlVXT1N0SEpza29oTkZHdk8KSnpNdUFvc2V2UGFWdElCSXBZbFgycUlaaHlhdyt2VW9BUTZYRnR3WjM1QWo1T1VPbVFQQUJWbkVXZUJZRzdSaQpaZmhEU2NTek5xb3ozWFpjMnA4a2VMWE1XOWJsTDNNOTdOMFRLbExuZ0NrSTdoaXJMVGE2T0E9PQotLS0tLUVORCBSU0EgUFJJVkFURSBLRVktLS0tLQo= "
}
```

```json
{
  "status": false,
  "info": "operate failed",
  "data": ""
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» info|string|true|none||none|
|» data|string|true|none||none|

## POST 新增工作节点(worker)

POST /pcapi/api/v1/cluster/common/new_worker

通过ssh远程调度安装kubernetes集群的工作节点，
并自动输入加入集群指令，完成工作节点注册

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cluster_type|query|string| 否 |集群类型,目前默认(只)支持kubernetes|
|host|query|string| 是 |安装控制节点的IP|
|port|query|integer| 是 |安装控制节点ssh端口|
|user|query|string| 是 |远程ssh认证用户|
|psssword|query|string| 是 |远程ssh认证密码|
|role|query|string| 是 |工作节点角色|
|join_command|query|string| 是 |加入集群指令|
|Authorization|header|string| 是 |base64加密ssh账号密码信息（示例是ysh,Kyy@123456）|

#### 详细说明

**Authorization**: base64加密ssh账号密码信息（示例是ysh,Kyy@123456）
用于pcapi服务校验客户端，下面是python写法
headers = basic_auth_headers('ssh账号', 'ssh密码')

> 返回示例

```json
{
  "status": true,
  "info": "operate success",
  "data": ""
}
```

```json
{
  "status": false,
  "info": "operate failed",
  "data": ""
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||状态|
|» info|string|true|none||详情|
|» data|string|true|none||数据|

## GET 获取某集群所有资源实例

GET /pcapi/api/v1/cluster/common/get_cluster_pods

通过拿到指定集群的ssh协议参数，
远程获取该集群下的所有计算资源实例信息

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|host|query|string| 是 |none|
|port|query|integer| 是 |none|
|user|query|string| 是 |none|
|psssword|query|string| 是 |none|
|Authorization|header|string| 是 |base64加密ssh账号密码信息（示例是ysh,Kyy@123456）|

#### 详细说明

**Authorization**: base64加密ssh账号密码信息（示例是ysh,Kyy@123456）
用于pcapi服务校验客户端，下面是python写法
headers = basic_auth_headers('ssh账号', 'ssh密码')

> 返回示例

```json
{
  "status": true,
  "info": "operate success",
  "data": {
    "total": 2,
    "rows": [
      {
        "pod_namespace": "my-namespace",
        "pod_name": "mysql-deployment-548dbbfc8f-dxltl",
        "pod_ready": "0/1",
        "pod_running": "ImagePullBackOff",
        "pod_restart": "0",
        "pod_age": "17h",
        "pod_ip": "10.244.5.3",
        "pod_node": "k8s-worker-20250408132243",
        "pod_nominated_node": "<none>",
        "pod_readiness_gates": "<none>"
      },
      {
        "pod_namespace": "my-namespace",
        "pod_name": "mysql-deployment-6fc6584bd6-6prqc",
        "pod_ready": "0/1",
        "pod_running": "ImagePullBackOff",
        "pod_restart": "0",
        "pod_age": "17h",
        "pod_ip": "10.244.5.6",
        "pod_node": "k8s-worker-20250408132243",
        "pod_nominated_node": "<none>",
        "pod_readiness_gates": "<none>"
      }
    ]
  }
}
```

```json
{
  "status": false,
  "info": "operate failed",
  "data": ""
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» info|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» rows|[object]|true|none||none|
|»»» pod_namespace|string|true|none||none|
|»»» pod_name|string|true|none||none|
|»»» pod_ready|string|true|none||none|
|»»» pod_running|string|true|none||none|
|»»» pod_restart|string|true|none||none|
|»»» pod_age|string|true|none||none|
|»»» pod_ip|string|true|none||none|
|»»» pod_node|string|true|none||none|
|»»» pod_nominated_node|string|true|none||none|
|»»» pod_readiness_gates|string|true|none||none|

## GET 获取某集群所有计算节点

GET /pcapi/api/v1/cluster/common/get_cluster_nodes

通过拿到指定集群的ssh协议参数，
远程获取该集群下的所有计算节点信息

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|host|query|string| 是 |none|
|port|query|integer| 是 |none|
|user|query|string| 是 |none|
|psssword|query|string| 是 |none|
|Authorization|header|string| 是 |base64加密ssh账号密码信息（示例是ysh,Kyy@123456）|

#### 详细说明

**Authorization**: base64加密ssh账号密码信息（示例是ysh,Kyy@123456）
用于pcapi服务校验客户端，下面是python写法
headers = basic_auth_headers('ssh账号', 'ssh密码')

> 返回示例

```json
{
  "status": true,
  "info": "operate success",
  "data": {
    "total": 2,
    "rows": [
      {
        "node_name": "k8s-master",
        "node_status": "Ready",
        "node_role": "control-plane",
        "node_age": "5d18h",
        "node_version": "v1.28.2",
        "node_internalip": "192.168.0.3",
        "node_externalip": "<none>",
        "node_osversion": "Ubuntu 22.04.1 LTS",
        "node_kernelversion": "5.15.0-91-generic",
        "node_containeruntime": "containerd://1.7.24"
      },
      {
        "node_name": "k8s-worker-20250408132243",
        "node_status": "Ready",
        "node_role": "<none>",
        "node_age": "21h",
        "node_version": "v1.28.2",
        "node_internalip": "192.168.0.2",
        "node_externalip": "<none>",
        "node_osversion": "Ubuntu 22.04.1 LTS",
        "node_kernelversion": "5.15.0-91-generic",
        "node_containeruntime": "containerd://1.7.24"
      }
    ]
  }
}
```

```json
{
  "status": false,
  "info": "operate failed",
  "data": ""
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» info|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» rows|[object]|true|none||none|
|»»» pod_namespace|string|true|none||none|
|»»» pod_name|string|true|none||none|
|»»» pod_ready|string|true|none||none|
|»»» pod_running|string|true|none||none|
|»»» pod_restart|string|true|none||none|
|»»» pod_age|string|true|none||none|
|»»» pod_ip|string|true|none||none|
|»»» pod_node|string|true|none||none|
|»»» pod_nominated_node|string|true|none||none|
|»»» pod_readiness_gates|string|true|none||none|

## POST 开发中-删除指定集群某工作节点

POST /pcapi/api/v1/cluster/common/delete_cluster_node

1.通过ssh协议及集群资源实例参数，远程删除指定集群下某计算资源实例，删除失败原因可能很多，统一在结果中告知
2.若强制删除，则系统先会标记该节点为不可用，再驱逐所有pod到其他节点，最后再删除

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|host|query|string| 是 |none|
|port|query|integer| 是 |none|
|user|query|string| 是 |none|
|psssword|query|string| 是 |none|
|node_name|query|string| 是 |节点名称(主机名)|
|force|query|boolean| 否 |是否强制删除(--force --grace-period=0选项)|
|Authorization|header|string| 是 |base64加密ssh账号密码信息（示例是ysh,Kyy@123456）|

#### 详细说明

**Authorization**: base64加密ssh账号密码信息（示例是ysh,Kyy@123456）
用于pcapi服务校验客户端，下面是python写法
headers = basic_auth_headers('ssh账号', 'ssh密码')

> 返回示例

```json
{
  "status": true,
  "info": "delete node success",
  "data": {
    "node_name": "k8s-worker-20250408132243",
    "force": true
  }
}
```

```json
{
  "status": false,
  "info": "delete node failed",
  "data": {
    "node_name": "k8s-worker-20250408132243",
    "force": true
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» info|string|true|none||none|
|» data|string|true|none||none|

## POST 开发中-切换某集群某工作节点状态

POST /pcapi/api/v1/cluster/common/node_state_switch

暂停/恢复kubernetes集群中某工作节点的可用状态，暂停即暂时不再接收新的pod调度

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|host|query|string| 是 |none|
|port|query|boolean| 是 |none|
|user|query|string| 是 |none|
|psssword|query|string| 是 |none|
|state|query|string| 是 |暂停还是恢复|
|darin|query|boolean| 否 |是否驱逐现有pod，默认不驱逐|
|Authorization|header|string| 是 |base64加密ssh账号密码信息（示例是ysh,Kyy@123456）|

#### 详细说明

**Authorization**: base64加密ssh账号密码信息（示例是ysh,Kyy@123456）
用于pcapi服务校验客户端，下面是python写法
headers = basic_auth_headers('ssh账号', 'ssh密码')

#### 枚举值

|属性|值|
|---|---|
|state|cordon|
|state|uncordon|

> 返回示例

```json
{
  "status": true,
  "info": "switch node success",
  "data": {
    "state": "cordon",
    "drain": false
  }
}
```

```json
{
  "status": false,
  "info": "switch node failed",
  "data": {
    "state": "uncordon",
    "drain": false
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» info|string|true|none||none|
|» data|object|true|none||none|
|»» node_name|string|true|none||none|
|»» force|boolean|true|none||none|

## POST 通过YAML实例化资源实例

POST /pcapi/api/v1/cluster/common/yaml_apply_delete

每次被调用都接收对方传来的新的yml文件内容，实例化k8s集群Pod资源，
其中包含创建，修改，删除kubernetes资源实例等操作

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cluster_type|query|string| 否 |集群类型  |
|host|query|string| 否 |主机地址  |
|port|query|integer| 否 |端口  |
|user|query|string| 否 |用户名  |
|psssword|query|string| 否 |密码  |
|kubeconfig|query|string| 否 |集群上下文  |
|action|query|string| 否 |操作  |
|namespace_name|query|string| 否 |命名空间名称 |
|serviceaccount_name|query|string| 否 |命名空间服务认证名称  |
|podcd_name|query|string| 否 |Pod引擎名称  |
|service_name|query|string| 否 |资源服务名称  |
|clusterid|query|string| 否 |集群ID  |
|cpcid|query|string| 否 |算力中心ID|
|source_name|query|string| 否 |资源名称  |
|instance_type|query|string| 否 |实例类型  |
|source_replicasetnum|query|string| 否 |副本数量  |
|source_authuser|query|string| 否 |认证用户名  |
|source_authpasswd|query|string| 否 |认证密码|
|source_podengine|query|string| 否 |Pod引擎类型  |
|pod_imagepath|query|string| 否 |基础镜像|
|source_memrate|query|string| 否 |内存限制  |
|source_cpurate|query|string| 否 |CPU 限制|
|source_selflabel|query|string| 否 |资源实例标签  |
|source_portmode|query|string| 否 |端口映射模式  |
|source_restartpolicy|query|string| 否 |重启策略  |
|source_apiport|query|string| 否 |集群内映射端口  |
|source_insideport|query|string| 否 |容器内监听端口  |
|source_outsideport|query|string| 否 |集群外映射端口  |
|source_mountpath|query|string| 否 |容器内挂载路径  |
|source_storagelimits|query|string| 否 |存储盘大小|
|Authorization|header|string| 是 |base64加密ssh账号密码信息（示例是ysh,Kyy@123456）|

#### 详细说明

**Authorization**: base64加密ssh账号密码信息（示例是ysh,Kyy@123456）
用于pcapi服务校验客户端，下面是python写法
headers = basic_auth_headers('ssh账号', 'ssh密码')

> 返回示例

```json
{
  "status": true,
  "info": "operate success",
  "data": null
}
```

```json
{
  "status": false,
  "info": "operate failed",
  "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» info|string|true|none||none|
|» data|string|true|none||none|

# pcapi_kboss容器云/算力中心管理

## GET 算力中心展示

GET /dev/cpcc/cpclist/get_cpclist.dspy

获取所有算力中心（列表信息），纯数据库操作

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|page|query|string| 否 |none|
|rows|query|string| 否 |none|
|sort|query|string| 否 |none|
|orgid|query|string| 否 |线下调试/非登录态可指定组织ID进行操作|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "算力中心数据查询成功",
  "data": {
    "total": 2,
    "rows": [
      {
        "id": "-z2r4CFb-7rcfugNn2wIr",
        "name": "首都算力中心1",
        "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
        "pcapi_url": "https://opencomputing.ai",
        "api_user": "ysh",
        "api_pwd": "Kyy@123456",
        "enable_date": "2025-05-16",
        "expire_date": "2026-06-17",
        "contactname": "Ahexl",
        "contactphone": "13141005621",
        "row_num_": 1
      },
      {
        "id": "AROU9udKtPNyh0AZtO_WY",
        "name": "测试pcapi",
        "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
        "pcapi_url": "https://trial.kaiyuancloud.cn",
        "api_user": "ysh",
        "api_pwd": "QUZVcXg5V1p1STMybG5Ia5XIAWA87bQMgZw=",
        "enable_date": "2025-04-13",
        "expire_date": "2025-04-18",
        "contactname": "kyy",
        "contactphone": "",
        "row_num_": 2
      }
    ]
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» total|integer|true|none||none|
|» rows|[object]|true|none||none|
|»» id|string|true|none||none|
|»» name|string|true|none||none|
|»» orgid|string|true|none||none|
|»» pcapi_url|string|true|none||none|
|»» api_user|string|true|none||none|
|»» api_pwd|string|true|none||none|
|»» enable_date|string|true|none||none|
|»» expire_date|string|true|none||none|
|»» contactname|string|true|none||none|
|»» contactphone|string|true|none||none|
|»» orgid_text|string|true|none||none|
|»» row_num_|integer|true|none||none|

## POST 算力中心添加

POST /dev/cpcc/cpclist/add_cpclist.dspy

添加算力中心，纯数据库操作

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|name|query|string| 是 |算力中心名称|
|pcapi_url|query|string| 是 |算力中心API总址|
|api_user|query|string| 是 |算力中心接口账号|
|api_pwd|query|string| 是 |算力中心接口密码|
|contactname|query|string| 是 |联系人|
|contactphone|query|string| 是 |手机号|
|enable_date|query|string| 否 |启用日期|
|expire_date|query|string| 否 |停用日期|
|orgid|query|string| 否 |线下调试/非登录态可指定组织ID进行操作|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "新建算力中心成功",
  "data": {
    "api_pwd": "Kyy@123456",
    "api_user": "ysh",
    "contactname": "Ahexl",
    "contactphone": "13141005621",
    "enable_date": "2025-05-16",
    "expire_date": "2026-06-17",
    "name": "首都算力中心1",
    "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
    "pcapi_url": "https://opencomputing.ai",
    "id": "9Luu-tbsJmEEcJxoAkumM"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» api_pwd|string|true|none||none|
|»» api_user|string|true|none||none|
|»» contactname|string|true|none||none|
|»» contactphone|string|true|none||none|
|»» enable_date|string|true|none||none|
|»» expire_date|string|true|none||none|
|»» name|string|true|none||none|
|»» orgid|string|true|none||none|
|»» pcapi_url|string|true|none||none|
|»» id|string|true|none||none|

## POST 算力中心更新

POST /dev/cpcc/cpclist/update_cpclist.dspy

更新某算力中心的基本数据，纯数据库操作

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|query|string| 是 |算力中心ID|
|name|query|string| 是 |算力中心名称|
|pcapi_url|query|string| 是 |算力中心API总址|
|api_user|query|string| 是 |算力中心接口账号|
|api_pwd|query|string| 是 |算力中心接口密码|
|contactname|query|string| 是 |联系人|
|contactphone|query|string| 是 |手机号|
|enable_date|query|string| 否 |启用日期|
|expire_date|query|string| 否 |停用日期|

> 返回示例

```json
{
  "status": true,
  "msg": "更新算力中心成功",
  "data": {
    "api_pwd": "QUZVcXg5V1p1STMybG5Ia5aL/gkv7+gmSkA=",
    "api_user": "修改后数据1",
    "contactname": "Ahexl",
    "contactphone": "13141005621",
    "enable_date": "2025-05-16",
    "expire_date": "2026-06-17",
    "id": "gOHOm7Wm01OPnBUFeeVi8",
    "name": "首都算力中心3",
    "pcapi_url": "https://opencomputing.ai"
  }
}
```

```json
{
  "status": false,
  "msg": "无算力中心ID"
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» widgettype|string|true|none||none|
|» options|object|true|none||none|
|»» title|string|true|none||none|
|»» cwidth|integer|true|none||none|
|»» cheight|integer|true|none||none|
|»» timeout|integer|true|none||none|
|»» message|string|true|none||none|

## POST 算力中心删除

POST /dev/cpcc/cpclist/delete_cpclist.dspy

删除某算力中心，纯数据库操作

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|query|string| 否 |算力中心展示接口返回的id|
|orgid|query|string| 否 |线下调试/非登录态可指定组织ID进行操作|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "删除算力中心成功",
  "data": {
    "id": "u8swLRSlyDt7IGpJurPVZ",
    "orgid": "mIWUHBeeDM8mwAFPIQ8pS"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» widgettype|string|true|none||none|
|» options|object|true|none||none|
|»» title|string|true|none||none|
|»» timeout|integer|true|none||none|
|»» cwidth|integer|true|none||none|
|»» cheight|integer|true|none||none|
|»» message|string|true|none||none|

# pcapi_kboss容器云/算力设备管理

## GET 算力设备展示

GET /dev/cpcc/cpcnode/get_cpcnode.dspy

输入算力中心id，展示该算力中心下所有算力设备，包含已安装的和未安装的

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心id|
|page|query|string| 否 |看哪页|
|rows|query|string| 否 |看多少行|
|sort|query|string| 否 |根据什么字段排序|

> 返回示例

```json
{
  "status": true,
  "msg": "获取算力设备成功",
  "data": {
    "total": 3,
    "rows": [
      {
        "id": "1cV3nLWGD_YLqXm9OUWKU",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "name": "2-虚拟机ubuntu2204",
        "clusterid": "4hBm8atruISOU2bs24t_N",
        "node_status": "1",
        "ip": "192.168.0.2",
        "devicetype": "0",
        "sshport": 22,
        "adminuser": "root",
        "adminpwd": "Yuanshenhong.1",
        "enable_date": "2025-03-31",
        "export_date": "2029-10-30",
        "external_ip": "未设置",
        "cpu_model": "STANDARD",
        "cpu_stock": 0,
        "memory_model": "STANDARD",
        "memory_stock": 0,
        "sysdisk_stock": 0,
        "datadisk_stock": 0,
        "gpu_model": "STANDARD",
        "gpu_stock": 0,
        "role": "worker",
        "node_status_text": "占用",
        "devicetype_text": "虚拟机",
        "row_num_": 1
      },
      {
        "id": "RJZ2GMHSWGVG7iRk_AJYm",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "name": "3-虚拟机ubuntu2204",
        "clusterid": "4hBm8atruISOU2bs24t_N",
        "node_status": "1",
        "ip": "192.168.0.3",
        "devicetype": "0",
        "sshport": 22,
        "adminuser": "root",
        "adminpwd": "Yuanshenhong.1",
        "enable_date": "2025-03-28",
        "export_date": "9999-12-31",
        "external_ip": "未设置",
        "cpu_model": "STANDARD",
        "cpu_stock": 0,
        "memory_model": "STANDARD",
        "memory_stock": 0,
        "sysdisk_stock": 0,
        "datadisk_stock": 0,
        "gpu_model": "STANDARD",
        "gpu_stock": 0,
        "role": "master",
        "node_status_text": "占用",
        "devicetype_text": "虚拟机",
        "row_num_": 2
      },
      {
        "id": "ULwkzAj-pF-RYkJde3hbS",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "name": "假算力设备",
        "clusterid": "4hBm8atruISOU2bs24t_X",
        "node_status": "0",
        "ip": "192.168.110.120",
        "devicetype": "1",
        "sshport": 22,
        "adminuser": "ysh",
        "adminpwd": "Kyy@123456",
        "enable_date": "2025-06-04",
        "export_date": "2025-06-04",
        "external_ip": "未设置",
        "cpu_model": "STANDARD",
        "cpu_stock": 0,
        "memory_model": "STANDARD",
        "memory_stock": 0,
        "sysdisk_stock": 0,
        "datadisk_stock": 0,
        "gpu_model": "STANDARD",
        "gpu_stock": 0,
        "role": "master",
        "node_status_text": "空闲",
        "devicetype_text": "物理机",
        "row_num_": 3
      }
    ]
  }
}
```

```json
{
  "status": false,
  "msg": "无算力中心ID"
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» rows|[object]|true|none||none|
|»»» id|string|true|none||设备id|
|»»» cpcid|string|true|none||算力中心id|
|»»» name|string|true|none||设备名称|
|»»» node_status|string|true|none||设备状态，占用/空闲|
|»»» clusterid|string|true|none||集群id|
|»»» ip|string|true|none||内网IP|
|»»» devicetype|string|true|none||设备类型，物理机/虚拟机|
|»»» sshport|integer|true|none||ssh端口|
|»»» adminuser|string|true|none||ssh用户|
|»»» adminpwd|string|true|none||ssh用户密码|
|»»» enable_date|string|true|none||启用日期|
|»»» export_date|string|true|none||结束日期|
|»»» external_ip|string|true|none||公网IP|
|»»» cpu_model|string|true|none||CPU硬件型号|
|»»» cpu_stock|integer|true|none||CPU核数量|
|»»» memory_model|string|true|none||内存硬件型号|
|»»» memory_stock|integer|true|none||内存大小（按Gi）|
|»»» sysdisk_stock|integer|true|none||系统盘大小（按Gi）|
|»»» datadisk_stock|integer|true|none||数据盘大小（按:Gi）|
|»»» gpu_model|string|true|none||GPU型号（格式:RTXABCD-32G）|
|»»» gpu_stock|integer|true|none||GPU卡数量|
|»»» node_status_text|string|true|none||none|
|»»» devicetype_text|string|true|none||none|
|»»» cluster_name|string|true|none||所属集群，默认为空|
|»»» role|string|true|none||集群角色，值为master：控制/worker：工作,默认为空|
|»»» row_num_|integer|true|none||none|

## POST 算力设备添加

POST /dev/cpcc/cpcnode/add_cpcnode.dspy

入网算力设备添加，纯数据库操作；
算力设备后续用作安装算力集群各角色节点

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心ID|
|ip|query|string| 是 |IP地址|
|name|query|string| 是 |设备简称|
|devicetype|query|string| 是 |设备类型，0是虚拟机，1是物理机|
|sshport|query|string| 是 |SSH端口|
|adminuser|query|string| 是 |管理账号|
|adminpwd|query|string| 是 |管理密码|
|node_status|query|string| 是 |算力设备状态，0是空闲，1是占用|
|external_ip|query|string| 是 |公网IP|
|cpu_model|query|string| 是 |CPU型号|
|cpu_stock|query|integer| 是 |CPU库存量，核为单位|
|memory_model|query|string| 是 |内存型号|
|memory_stock|query|integer| 是 |内存库存量，Gi为单位|
|sysdisk_stock|query|integer| 是 |系统盘库存量，Gi为单位|
|datadisk_stock|query|integer| 是 |数据盘库存量，Gi为单位|
|gpu_model|query|string| 是 |GPU型号|
|gpu_stock|query|integer| 是 |GPU库存量，卡为单位|
|role|query|string| 是 |集群角色|
|enable_date|query|string| 否 |启用日期|
|export_date|query|string| 否 |停用日期|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "新增算力设备成功",
  "data": {
    "adminpwd": "QUZVcXg5V1p1STMybG5Ia5aL/gkv7+gmSkA=",
    "adminuser": "ysh",
    "cpcid": "AROU9udKtPNyh0AZtO_WY",
    "devicetype": "1",
    "enable_date": "2025-05-16",
    "export_date": "2026-06-17",
    "ip": "192.168.0.8",
    "name": "gpu设备1",
    "node_status": "0",
    "sshport": "22",
    "id": "DeolAhhh_sE6UE9DMqDSa"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» widgettype|string|true|none||none|
|» options|object|true|none||none|
|»» user_data|object|true|none||none|
|»»» _webbricks_|[string]|true|none||none|
|»»» width|[string]|true|none||none|
|»»» height|[string]|true|none||none|
|»»» _is_mobile|[string]|true|none||none|
|»»» cpcid|string|true|none||none|
|»»» ip|string|true|none||none|
|»»» name|string|true|none||none|
|»»» devicetype|string|true|none||none|
|»»» sshport|string|true|none||none|
|»»» adminuser|string|true|none||none|
|»»» adminpwd|string|true|none||none|
|»»» node_status|string|true|none||none|
|»»» enable_date|string|true|none||none|
|»»» export_date|string|true|none||none|
|»»» id|string|true|none||none|
|»» cwidth|integer|true|none||none|
|»» cheight|integer|true|none||none|
|»» title|string|true|none||none|
|»» timeout|integer|true|none||none|
|»» message|string|true|none||none|

## POST 算力设备更新

POST /dev/cpcc/cpcnode/update_cpcnode.dspy

更新某算力设备基本信息，
更新时密码加密那块每次都会加密，建议取消那块逻辑

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|query|string| 是 |算力设备ID|
|cpcid|query|string| 是 |算力中心ID|
|ip|query|string| 是 |IP地址|
|name|query|string| 是 |设备简称|
|devicetype|query|string| 是 |设备类型，0是虚拟机，1是物理机|
|sshport|query|string| 是 |SSH端口|
|adminuser|query|string| 是 |管理账号|
|adminpwd|query|string| 是 |管理密码|
|node_status|query|string| 是 |算力设备状态|
|external_ip|query|string| 是 |公网IP|
|cpu_model|query|string| 是 |CPU型号|
|cpu_stock|query|integer| 是 |CPU库存量，核为单位|
|memory_model|query|string| 是 |内存型号|
|memory_stock|query|integer| 是 |内存库存量，Gi为单位|
|sysdisk_stock|query|integer| 是 |系统盘库存量，Gi为单位|
|datadisk_stock|query|integer| 是 |数据盘库存量，Gi为单位|
|gpu_model|query|string| 是 |GPU型号|
|gpu_stock|query|integer| 是 |GPU库存量，卡为单位|
|role|query|string| 是 |集群角色|
|enable_date|query|string| 否 |启用日期|
|export_date|query|string| 否 |停用日期|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "更新算力中心成功",
  "data": {
    "adminpwd": "Kyy@123456",
    "adminuser": "ysh",
    "cpcid": "AROU9udKtPNyh0AZtO_WY",
    "devicetype": "1",
    "enable_date": "2025-05-16",
    "export_date": "2026-06-17",
    "id": "E71hIuIKvTr5D2w2Sxnc9",
    "ip": "192.168.0.8",
    "name": "gpu设备122cccc",
    "node_status": "0",
    "sshport": "22"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» widgettype|string|true|none||none|
|» options|object|true|none||none|
|»» title|string|true|none||none|
|»» cwidth|integer|true|none||none|
|»» cheight|integer|true|none||none|
|»» timeout|integer|true|none||none|
|»» message|string|true|none||none|

## POST 算力设备移除

POST /dev/cpcc/cpcnode/delete_cpcnode.dspy

移除算力中心中的某个算力设备，建议交互方式使用DELETE方法

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|query|string| 否 |算力设备查找返回的id|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "删除算力设备成功",
  "data": {
    "id": "Za8rOOFoacMZnbKoTVig2"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» widgettype|string|true|none||none|
|» options|object|true|none||none|
|»» title|string|true|none||none|
|»» timeout|integer|true|none||none|
|»» cwidth|integer|true|none||none|
|»» cheight|integer|true|none||none|
|»» message|string|true|none||none|

# pcapi_kboss容器云/标签管理

## GET 获取资源标签

GET /dev/cpcc/cpclabel/get_cpclabel.dspy

获取该算力中心下的所有资源标签，展示时尽量每行一个键值对

在新增资源实例配置接口前需要，同步获取相应节点标签，下拉框进行选择（传 {key 单位 value} 给后端）

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|orgid|query|string| 否 |用户组织id|

> 返回示例

```json
{
  "status": true,
  "msg": "获取资源标签成功",
  "data": {
    "total": 4,
    "rows": [
      {
        "id": "3h1CPE1jv7TwF52A4urJd",
        "name": "非GPU设备",
        "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
        "labeltype": "1",
        "label_key": "kyy-gpu",
        "symbol": "=",
        "label_value": "false",
        "update_time": "2025-05-28 14:42:04",
        "row_num_": 1
      },
      {
        "id": "APP5429j81a4kBmmrhi52",
        "name": "GPU设备",
        "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
        "labeltype": "1",
        "label_key": "kyy-gpu",
        "symbol": "=",
        "label_value": "true",
        "update_time": "2025-05-28 14:42:06",
        "row_num_": 2
      },
      {
        "id": "Fx1xo6bXcFLp9pLLXgpRN",
        "name": "测试标签",
        "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
        "labeltype": "0",
        "label_key": "kyy-test",
        "symbol": ":",
        "label_value": "ok",
        "update_time": "2025-05-28 14:42:21",
        "row_num_": 3
      },
      {
        "id": "mfbiVzlAtd87H1cX_b81X",
        "name": "cd",
        "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
        "labeltype": "0",
        "label_key": "kyy-we",
        "symbol": ":",
        "label_value": "qwe",
        "update_time": "2025-05-28 14:42:24",
        "row_num_": 4
      }
    ]
  }
}
```

```json
{
  "status": false,
  "msg": "无算力中心id"
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» rows|[object]|true|none||none|
|»»» id|string|true|none|标签id|none|
|»»» name|string|true|none|标签名称|none|
|»»» orgid|string|true|none|用户组织id|none|
|»»» labeltype|string|true|none|标签类型|哪种资源的标签，0是实例标签，1是节点标签，后续再拓展其它|
|»»» label_key|string|true|none|标签属性|none|
|»»» symbol|string|true|none|等价符号|= 是节点标签， ：是资源标签|
|»»» label_value|string|true|none|标签值|none|
|»»» update_time|string|true|none|更新时间|none|
|»»» row_num_|integer|true|none||none|

## POST 新增资源标签

POST /dev/cpcc/cpclabel/add_cpclabel.dspy

新增资源标签

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|name|query|string| 是 |标签名称|
|labeltype|query|string| 是 |哪种资源的标签，0是实例标签，1是节点标签，后续再拓展其它|
|label_key|query|string| 是 |标签属性|
|label_value|query|string| 是 |标签属性值|
|orgid|query|string| 否 |用户组织id|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "新增资源标签成功",
  "data": {
    "label_key": "kyy-app",
    "label_value": "mysql8",
    "labeltype": "0",
    "name": "mysql8资源实例",
    "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
    "id": "BvJGOTjpDelumxH5Uo0Qz",
    "update_time": "2025-05-27 14:13:00"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 删除资源标签

POST /dev/cpcc/cpclabel/delete_cpclabel.dspy

删除资源标签

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|query|string| 是 |标签列表返回的id|
|orgid|query|string| 否 |用户组织id|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "删除资源标签成功",
  "data": {
    "id": "6bi3hfxxVqMM7hy-OuitEa"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 集群节点绑定/解绑标签

POST /dev/cpcc/cpclabel/setup_cpclabel.dspy

给指定算力中心里某集群中的工作节点绑定标签/解绑标签

一次只能一个标签

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心id|
|clusterid|query|string| 是 |算力集群id|
|label|query|string| 是 |单个标签内容|
|worker_node|query|string| 是 |集群某节点（页面返回的节点名）|
|opt|query|string| 是 |操作，label是绑定，unlabel是解绑|
|orgid|query|string| 否 |用户组织id|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "设置节点标签成功",
  "data": {
    "clusterid": "4hBm8atruISOU2bs24t_N",
    "cpcid": "AROU9udKtPNyh0AZtO_WY",
    "label": "kyy-gpu=false",
    "opt": "label",
    "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
    "worker_node": "k8s-worker-20250408132243"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# pcapi_kboss容器云/算力集群管理

## GET 获取多算力集群信息

GET /dev/cpcc/cpccluster/get_cpccluster.dspy

输入算力中心ID，展示该算力中心下所有kubernetes集群信息

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心id|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "获取算力集群成功",
  "data": {
    "total": 1,
    "rows": [
      {
        "id": "4hBm8atruISOU2bs24t_N",
        "name": "测试离线安装控制节点",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "clustertype": "0",
        "controllerid": "RJZ2GMHSWGVG7iRk_AJYm",
        "enable_date": "2025-04-03",
        "export_date": "2025-05-10",
        "clusterjoin": "kubeadm join 192.168.0.3:6443 --token nt80u6.gzpj9dxsrw79270c --discovery-token-ca-cert-hash sha256:7b33439b2a1b37a8d8938513bd45405f57c3255771c3b9b9b90af448d886b0c2",
        "kubeconfig": "apiVersion: v1\nclusters:\n- cluster:\n    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJBZ0lJTGd4THlGMjM3QmN3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TlRBME1ETXdOelE1TXpWYUZ3MHpOVEEwTURFd056VTBNelZhTUJVeApFekFSQmdOVkJBTVRDbXQxWW1WeWJtVjBaWE13Z2dFaU1BMEdDU3FHU0liM0RRRUJBUVVBQTRJQkR3QXdnZ0VLCkFvSUJBUURQUm5hdkZmNXBTWWUvVmJLc0s2SnhEazhyc2hsc2h5WnNNRk8xZDVhZG45Z055T0wwR2NtbEsrQ1EKVklKSnF3RklJeSsxUVlEd3VRMytzczEwYmV2Y2lqM1BRanluaXJRRkNhRlA0NHh2ZkEyK2thV1FYeTVncGwrMwpjSkI1K1MxVmx2Vi9aSHQ5SXgwNjFCdHB4dE5oMUkxNS9IYk4rWmVNNnEvd3lxUW93Y01ub2pyNDltYkxxOWNwCnFSem5LL2FwWXlBYnljUk9uWWlIZ0FjQWdsclFOTjBKUEJZd2dRd0pIUmlIcGhtVFBkdmY2ckxkNFR0dFl2OXgKdmZIRDNjVUdwZkVBUElaNUJBVi9ZM3p5V0pSbDQzSFV2Ri9jemNDQ01jOVlUd3VXaEpxb2doUUZUdnNuSVZzTwovNEtKQzRwQXFSenJlZFRWdExmMXgzQlRpVCt0QWdNQkFBR2pXVEJYTUE0R0ExVWREd0VCL3dRRUF3SUNwREFQCkJnTlZIUk1CQWY4RUJUQURBUUgvTUIwR0ExVWREZ1FXQkJUZjRZbzBpOVpIZC9ObzdkYWZrZVRTbzVzdzN6QVYKQmdOVkhSRUVEakFNZ2dwcmRXSmxjbTVsZEdWek1BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRRERLalJWVVp1YwppckJ4QWdZWnBBeW5NSHdWQTF6YStVT09FM1U0MEMyVTN0VGgrK1BsN2o2ZGJZTWNWdEFvTXhxaDRiVjNQRW5SCmtWcWNaN2NjS3FGSXduZlhHK0ZGTVVwazVoTk0xLzc2UXBobi9OWk8zSStSVjFtV0VOU1BzM1FZdEVoWktXUlgKYWRXZ0krK0x1cUZyZVpTVzVjRXNnMWZDODFtd3dhTXdkRHZWcFJZMFEwWlBsMGFqTURsSlNDaDNOSXpQOS82bwpndXBrY1JSdWtvRGlscWVraXlrRWJ5OVJCWHZIbXo3Q0sxQ1ZnZXZJTDZrVnRPRFF2Rm10Qm1WemlRNWFDcXJOCmtZNmd6OUNGMkdKc2M4UkZrcWQxbzdMelhPakJsTkdzN2k2WmdEOE1Ca2tiank2RmZDZWVndmxOOGFCU2VmblEKZ2ZNOVptbnRpMVNDCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K\n    server: https://192.168.0.3:6443\n  name: kubernetes\ncontexts:\n- context:\n    cluster: kubernetes\n    user: kubernetes-admin\n  name: kubernetes-admin@kubernetes\ncurrent-context: kubernetes-admin@kubernetes\nkind: Config\npreferences: {}\nusers:\n- name: kubernetes-admin\n  user:\n    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURJRENDQWdpZ0F3SUJBZ0lIVGZPdmU4TzBJVEFOQmdrcWhraUc5dzBCQVFzRkFEQVZNUk13RVFZRFZRUUQKRXdwcmRXSmxjbTVsZEdWek1CNFhEVEkxTURRd016QTNORGt6TlZvWERUSTJNRFF3TXpBM05UUXpOMW93TkRFWApNQlVHQTFVRUNoTU9jM2x6ZEdWdE9tMWhjM1JsY25NeEdUQVhCZ05WQkFNVEVHdDFZbVZ5Ym1WMFpYTXRZV1J0CmFXNHdnZ0VpTUEwR0NTcUdTSWIzRFFFQkFRVUFBNElCRHdBd2dnRUtBb0lCQVFEWVJJT3h0TWFkOWs2T1JsL1UKZ2ZnZVJDQkpjZmMrc2ZFbzkxeW4vc05KZFVIbWRuamtMaC9wRjcwZkdoVWZ3R2t5dzR0WkdpTFFNR0xwclpyeAphVTdJT0R3a3I2ejl1SkQzaHlFZExhZGpZT0NOMHJhUFNpV05GV1QwSVN2UVBjZzNGQkQ2YmFHb2RtSmN5YnBPCk5qY1VZZmh5WEVqRXMwOU92QzhhZUJCbm9Na1RkRk53dlFaYXE2LzR3eTUyN0k3aUdIUVdvL21JS1VUVHhzRFgKMzJnVXErZmRVMEh5STJJeWhNMGdwT29uNURCVmRUbWsyMkZsVHk0ZWJ3Q3R4QmMvRCtpelhuZFpVd2tHMExMVwpqTEc4L3JkWTZ4WFJDVkhHM1BWNURRK0JvNEpnMTUwWWFSUnBKeDJYSGxad3N5OFBZcWVLcTM0b1pxczRTRndmCjJCY3JBZ01CQUFHalZqQlVNQTRHQTFVZER3RUIvd1FFQXdJRm9EQVRCZ05WSFNVRUREQUtCZ2dyQmdFRkJRY0QKQWpBTUJnTlZIUk1CQWY4RUFqQUFNQjhHQTFVZEl3UVlNQmFBRk4vaGlqU0wxa2QzODJqdDFwK1I1TktqbXpEZgpNQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUJBUUFTR0phc1EyQXpLdVNZWFdtMGlYOUhnWTNZQUJGMHpYRzRKZU5lCjREekxkOHF2TXlqRGMwUWFWSUtNbWswemhrV1ZIQzNKSEZWalRXcDBUNFE0TlVBMk8rOXFob1p0a25NL3dsQlUKS0Zab3ZHNFd6SU1sdVJwL21ZRUIzL3dHbkFPV01MdEtBSWJ3d3FRVWl4VW5KYkxCeG4xQ1k5ZERzb1o4VmZZMQp4N2R0WDBJWjJkbU1ETTVLV1lrbW5tQWJBR0tXazZBR3pVWEpWNmlTU3laYjlWLzNuN3hmZlpZRkVDQXBQNk91CjhmRGdIVjBCdEMxS3VmU0tsTitLMnF2aXAzMlRjRHdoTEVHQWQ2aU9qYzhBRXlHelJmOWY4M0xUSGJ2dGtibjYKR0VQQlBQSExSTFlQWEh0OE9LbHdNOThwQWxkSkIyWEJ6UEttc0JFeGFOSWRXd2FTCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K\n    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBMkVTRHNiVEduZlpPamtaZjFJSDRIa1FnU1hIM1BySHhLUGRjcC83RFNYVkI1blo0CjVDNGY2UmU5SHhvVkg4QnBNc09MV1JvaTBEQmk2YTJhOFdsT3lEZzhKSytzL2JpUTk0Y2hIUzJuWTJEZ2pkSzIKajBvbGpSVms5Q0VyMEQzSU54UVErbTJocUhaaVhNbTZUalkzRkdINGNseEl4TE5QVHJ3dkduZ1FaNkRKRTNSVApjTDBHV3F1ditNTXVkdXlPNGhoMEZxUDVpQ2xFMDhiQTE5OW9GS3ZuM1ZOQjhpTmlNb1ROSUtUcUorUXdWWFU1CnBOdGhaVTh1SG04QXJjUVhQdy9vczE1M1dWTUpCdEN5MW95eHZQNjNXT3NWMFFsUnh0ejFlUTBQZ2FPQ1lOZWQKR0drVWFTY2RseDVXY0xNdkQyS25pcXQrS0dhck9FaGNIOWdYS3dJREFRQUJBb0lCQVFDQ1djRjZ3YmdaQzVWTApvZFV1MCt1RjZvLy9WS2F1YmpncDlmWXQ5NXNqVW42Vzl2OWtvUHh3MVBNVHBQZm9mR09yeWpyYVNLdUZDalVFCkhiUlBINmJ4ZlJ1YkRSdmFqWDByQkpLTDhMRjhiNjdKTEtFR2VxMXBmT1N0VkxVQXZjeElqbHF4WnBUU1loQmwKVnQxcE9MbzRHZGpTclJiYklDeUVDMTdrdUV0QytZV3lFb3E5MmlLNVdMTHdHM2hwVzhyVlVLVzZ2T0cyd0l4bAp0RWhMSGpOOWtnb1VVa2pORG9tK2FlcVVxeXhDeUZEdll4UmdhVTd0Y3pJSk52SUk3aDYxaExQbEZtMmxGQ0xlCjhjeTdKUDMyV1ZDSUpUMHhRNkJJRTdvVld4WWIvMzFVSHYrTHg0UHlBcFpiZ3piMjlvQm54VjhneUxnVjZDWW0Kd1psQlQ4S2hBb0dCQU9tMFZqTkVHVm5EaXNsTDFVVkNKYzFCVU1KcjNwalQvV0g4d2s0UzJYWmhwRWdVQmpQYgpDM3Y5czkxNHh6SjhXYWFtUFZPVGZMRmxzRWFLNnJpMFhjQkhXQi9ob1R1aDVKaDByS1RNWWFMTm9SdU00VCt6Ci9zUG1aY1ZMVXcxdHFmd3U5YlVpSTJCQURQNFM2MUFubk5hSnF1UmFWRk8vT1pqZUkvbHJzMVBSQW9HQkFPem0KVTNvcjNuSDh4WHI2WDNJUjRDM3l3TkZLaHNVVE44VmdWNWRVL0U5RmRHTldUVzRkWHdCK01jeUlQMlFLbjlycwpmcU9Cb0c3NlRKVHF0YzVobjY5Q014c1lVNVdPcDhOZW9oaXplY1luSTFjTk94TmZwdzZDdUZVb1pmTFFxU1dICmJ4dEVEaFkrcXJjR2FLZ3VzMk1uMkJ2cEg1bUhCTk5DL05pSVZ1WTdBb0dBZFlnVEhkOHVuSjBockJCdUpsR1kKN3p2YzRKb2RMV0RYZWpNQ2lQOGp6RXhZc1VNWXgzVnV0aUdtRmtpS2JWSnFSOHdzNVY0MEJJY3VlcHVjWmQyWApsSDZNekNQTjBVNmV4eWxPTmVidlowL2dxUmxWb3BMa0dpTkJwVkkzWjNaeVdYaElhNXJLamJwSWpuSjNVeTFJCnpBQWFLSk5nKzJrZEQwc1FibnlDaURFQ2dZQVFDZVA2OEg5bDdqd2NnRmozNnhmblpIa0RjbTAvYUhhdEtVR2sKNEQ4WXl0WC9aN2RrVGg3QmRNbkFWRFVlZTgyb3o3d2ZLOGFGM1BKVVhyT2lYbCttU1BBVzFJWE1LVlZZVjg3WApwMGNHVUY0SEpjRXJKWjIwME1yVUVTRWQyRnlyU3NrTjZvU2RvdTZCNTdBc09zVXdZR0UwT290R0pLc0I5cFlSCnZ1RkxRd0tCZ1FEZVFuRElPaUQ2SEpmc2loTC8xZ3dnS0hVeVc2WGYrNFhQODd3ZlVXT1N0SEpza29oTkZHdk8KSnpNdUFvc2V2UGFWdElCSXBZbFgycUlaaHlhdyt2VW9BUTZYRnR3WjM1QWo1T1VPbVFQQUJWbkVXZUJZRzdSaQpaZmhEU2NTek5xb3ozWFpjMnA4a2VMWE1XOWJsTDNNOTdOMFRLbExuZ0NrSTdoaXJMVGE2T0E9PQotLS0tLUVORCBSU0EgUFJJVkFURSBLRVktLS0tLQo=",
        "clustertype_text": "kubernetes",
        "controllerid_text": "192.168.0.3",
        "row_num_": 1
      }
    ]
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» total|integer|true|none||none|
|» rows|[object]|true|none||none|
|»» id|string|false|none||none|
|»» name|string|false|none||集群名称|
|»» cpcid|string|false|none||所属算力中心，前端转ID为名称|
|»» clustertype|string|false|none||集群类型，前端不显示|
|»» controllerid|string|false|none||控制节点，前端不显示|
|»» enable_date|string|false|none||启用日期|
|»» clusterjoin|string|false|none||集群注册码|
|»» export_date|string|false|none||停止日期|
|»» kubeconfig|string|false|none||集群上下文，前端隐藏，给pcapi用的|
|»» clustertype_text|string|false|none||集群类型文字|
|»» controllerid_text|string|false|none||控制节点文字|
|»» ready|integer|true|none||集群状态，0:正在安装，1:安装完成|
|»» row_num_|integer|false|none||none|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|

## POST 算力集群基础信息更新

POST /dev/cpcc/cpccluster/update_cpccluster.dspy

修改某算力集群的基础信息

注意：前端需要处理一下，只能修改集群名称和两个时间参数，其他参数不允许修改！！！

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |所属算力中心ID|
|id|query|string| 是 |算力集群id|
|controllerid|query|string| 否 |集群控制节点id|
|name|query|string| 否 |集群名称|
|cluster_type|query|string| 否 |集群类型，0为kubernetes，1为slurm|
|clusterjoin|query|string| 否 |集群注册码|
|enable_date|query|string| 否 |启用时间|
|export_date|query|string| 否 |停止时间|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 获取空闲的算力设备

GET /dev/cpcc/cpcnode/get_cpcidle_device.dspy

用于创建集群时选择空闲设备（选择IP）。

注意：创建集群或新增集群工作节点时需要先获取到空闲状态的算力设备(IP)！！！

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心id|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "获取空闲设备成功",
  "data": [
    {
      "id": "XLUBumc_RzHBStQfpi5u0",
      "name": "gpu设备1",
      "clusterid": null,
      "node_status": "0",
      "ip": "192.168.0.8",
      "devicetype": "1",
      "sshport": 22,
      "adminuser": "ysh",
      "adminpwd": "Kyy@123456",
      "cpcid": "AROU9udKtPNyh0AZtO_WY",
      "enable_date": "2025-05-16",
      "export_date": "2026-06-17"
    }
  ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» id|string|true|none||none|
|» ip|string|true|none||none|
|» node_status|string|true|none||0空闲，1占用|

## GET 实时集群资源实例看板

GET /dev/cpcc/cpcpod/get_cpcpod.dspy

查看实时集群资源实例信息，字段解释详见下方

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心ID|
|clusterid|query|string| 是 |算力集群ID|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "获取集群实时资源实例成功",
  "data": {
    "total": 1,
    "rows": [
      {
        "pod_namespace": "4hbm8atruisou2bs24t-n-miwuhbeedm8mwafpiq8ps",
        "pod_name": "q2aodptfquogblu5nzblt-statefulset-0",
        "pod_ready": "1/1",
        "pod_running": "Running",
        "pod_restart": "0",
        "pod_age": "16h",
        "pod_ip": "10.244.5.36",
        "pod_node": "k8s-worker-20250408132243",
        "pod_nominated_node": "无",
        "pod_cpurate": "0.004核",
        "pod_memrate": "2.539Mi",
        "pod_gpu": "0",
        "pod_cpu_limit": "2",
        "pod_memory_limit": "5Gi",
        "pod_gpu_limit": "0"
      }
    ]
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» rows|[object]|true|none||none|
|»»» pod_namespace|string|true|none|命名空间|none|
|»»» pod_name|string|true|none|资源实例名称|none|
|»»» pod_ready|string|true|none|就绪状态|none|
|»»» pod_running|string|true|none|运行状态|none|
|»»» pod_restart|string|true|none|重启次数|none|
|»»» pod_age|string|true|none| 运行时长|d是天，h是小时，m是分钟，s是秒|
|»»» pod_ip|string|true|none|集群内部IP|none|
|»»» pod_node|string|true|none|Pod节点主机名|none|
|»»» pod_nominated_node|string|true|none|指定节点/调度模式|默认值：自动调度|
|»»» pod_cpurate|string|true|none| cpu使用数|none|
|»»» pod_memrate|string|true|none|内存使用数|none|
|»»» pod_gpu|string|true|none|GPU使用数|none|
|»»» pod_cpu_limit|string|true|none|CPU限制|none|
|»»» pod_memory_limit|string|true|none|内存限制|none|
|»»» pod_gpu_limit|string|true|none|GPU限制|none|
|»»» pod_readiness_gates|[string]|true|none||none|

## GET 实时集群成员节点看板

GET /dev/cpcc/cpcworker/get_cpcworker.dspy

查看试试集群成员节点列表信息，字段解释详见下方

给pcapi的人看的

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心ID|
|clusterid|query|string| 是 |算力集群ID|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "获取集群实时成员节点成功",
  "data": {
    "total": 2,
    "rows": [
      {
        "node_name": "k8s-master",
        "node_status": "已就绪",
        "node_role": "控制节点",
        "node_age": "70d",
        "node_version": "v1.28.2",
        "node_internalip": "192.168.0.3",
        "node_externalip": "未分配",
        "node_osversion": "Ubuntu 22.04.1 LTS",
        "node_kernelversion": "5.15.0-91-generic",
        "node_containeruntime": "containerd://1.7.24",
        "node_labels": [
          "kyy-gpu=false"
        ],
        "node_cpurate": "21.2%",
        "node_memrate": "1.4%",
        "node_gpu": "0%",
        "available_cpu": "3.15核",
        "available_memory": "15.30Gi",
        "available_gpu": 0
      },
      {
        "node_name": "k8s-worker-20250408132243",
        "node_status": "已就绪",
        "node_role": "工作节点",
        "node_age": "65d",
        "node_version": "v1.28.2",
        "node_internalip": "192.168.0.2",
        "node_externalip": "未分配",
        "node_osversion": "Ubuntu 22.04.1 LTS",
        "node_kernelversion": "5.15.0-91-generic",
        "node_containeruntime": "containerd://1.7.24",
        "node_labels": [
          "kyy-gpu=false"
        ],
        "node_cpurate": "60.0%",
        "node_memrate": "34.8%",
        "node_gpu": "0%",
        "available_cpu": "1.60核",
        "available_memory": "10.11Gi",
        "available_gpu": 0
      }
    ]
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» rows|[object]|true|none||none|
|»»» node_name|string|true|none|主机名|none|
|»»» node_status|string|true|none|运行状态|none|
|»»» node_role|string|true|none|节点角色|none|
|»»» node_age|string|true|none|运行时长|none|
|»»» node_version|string|true|none|kubernetes版本|none|
|»»» node_internalip|string|true|none|内网IP|none|
|»»» node_externalip|string|true|none|外网IP|none|
|»»» node_osversion|string|true|none|操作系统版本|none|
|»»» node_kernelversion|string|true|none|内核版本|none|
|»»» node_containeruntime|string|true|none|容器运行时版本|none|
|»»» node_labels|[string]|true|none|节点标签|none|
|»»» node_cpurate|string|true|none|CPU利用率|none|
|»»» node_memrate|string|true|none|内存利用率|none|
|»»» node_gpu|string|true|none|GPU利用率|none|
|»»» available_cpu|string|true|none|可用CPU|none|
|»»» available_memory|string|true|none|可用内存|none|
|»»» available_gpu|integer|true|none|可用GPU|none|

## POST 新增集群资源实例配置

POST /dev/cpcc/cpcpodyaml/new_cpcpodyaml.dspy

1.通过pcapi_kboss前端输入资源实例参数/操作指令给pcapi_kboss后端，再中转给算力中心pcapi服务进行kubernetes核心API操作，级联创建相应的资源实例；
2.目前算力中心pcapi服务有且仅支持Linux操作系统Ubuntu:22.04和关系型数据库MySQL:8.0；
3.算力中心pcapi服务操作结果返回给pcapi_kboss后端，pcapi_kboss后端再反馈给前端操作结果即可。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|clusterid|query|string| 是 |集群唯一标识ID|
|source_name|query|string| 是 |资源实例的名称|
|source_authuser|query|string| 是 |初始认证账号|
|source_authpasswd|query|string| 是 |初始认证密码|
|source_podengine|query|string| 是 |资源实例控制器，下拉框，默认StatefulSet，Deployment，DaemonSet，CronJob，Job，Standalone|
|source_replicasetnum|query|string| 是 |HPA副本数|
|instance_type|query|string| 是 |资源实例类型，下拉框，默认LinuxOS为Linux操作系统，RelationalDB为关系型数据库|
|pod_imagepath|query|string| 是 |基础镜像，下拉框，默认docker.io/library/ubuntu:22.04，docker.io/library/mysql:8.0，docker.io/jupyter/base-notebook:latest|
|source_memrate|query|string| 是 |内存资源限制|
|source_cpurate|query|string| 是 |CPU资源限制|
|source_selflabel|query|string| 是 |自定义标签，用于资源分类|
|source_gpu|query|string| 是 |分配GPU个数|
|source_portmode|query|string| 是 |服务暴露的端口模式，下拉框，默认NodePort，Ingress，LoadBalancer|
|source_restartpolicy|query|string| 是 |容器重启策略，下拉框，默认Always，OnFailure，Never|
|source_apiport|query|string| 是 |服务对外提供的端口|
|source_insideport|query|string| 是 |容器内部监听的端口|
|source_outsideport|query|string| 是 |通过NodePort暴露的节点端口|
|source_mountpath|query|string| 是 |容器内的挂载路径|
|source_storagelimits|query|string| 是 |存储资源限制|
|source_nodeselector|query|string| 是 |节点选择器|
|orgid|query|string| 否 |线下调试/非登录态可指定组织ID进行操作|
|cpu_model|query|string| 是 |CPU型号|
|gpu_model|query|string| 是 |显卡型号|
|disk_sys_limit|query|string| 是 |默认系统盘空间|
|userid|query|string| 否 |none|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "新增资源实例参数成功,请10秒后查看实时资源实例面板",
  "data": {
    "action": "apply",
    "namespace_name": "4hbm8atruisou2bs24t-n-miwuhbeedm8mwafpiq8ps",
    "serviceaccount_name": "4hbm8atruisou2bs24t-n-miwuhbeedm8mwafpiq8ps-serviceaccount",
    "podcd_name": "evfldtxjkr3jd8zxnfhd5-statefulset",
    "service_name": "evfldtxjkr3jd8zxnfhd5-service",
    "instance_type": "LinuxOS",
    "clusterid": "4hBm8atruISOU2bs24t_N",
    "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
    "pod_imagepath": "docker.io/library/ubuntu:22.04",
    "source_apiport": "6035",
    "source_authpasswd": "kyycloud",
    "source_authuser": "root",
    "source_cpurate": "1000m",
    "source_insideport": "3306",
    "source_memrate": "512Mi",
    "source_mountpath": "/mnt/data",
    "source_name": "kyy-new5090gpu-ubuntu2204",
    "source_outsideport": "30063",
    "source_podengine": "StatefulSet",
    "source_portmode": "NodePort",
    "source_replicasetnum": "1",
    "source_restartpolicy": "Always",
    "source_selflabel": "app:ubuntu3",
    "source_storagelimits": "49Gi",
    "source_nodeselector": "kyy-gpu=false",
    "id": "evfldtxjkr3jd8zxnfhd5",
    "cpcid": "AROU9udKtPNyh0AZtO_WY"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» action|string|true|none||none|
|»» namespace_name|string|true|none||none|
|»» serviceaccount_name|string|true|none||none|
|»» podcd_name|string|true|none||none|
|»» service_name|string|true|none||none|
|»» instance_type|string|true|none||none|
|»» clusterid|string|true|none||none|
|»» orgid|string|true|none||none|
|»» pod_imagepath|string|true|none||none|
|»» source_apiport|string|true|none||none|
|»» source_authpasswd|string|true|none||none|
|»» source_authuser|string|true|none||none|
|»» source_cpurate|string|true|none||none|
|»» source_insideport|string|true|none||none|
|»» source_memrate|string|true|none||none|
|»» source_mountpath|string|true|none||none|
|»» source_name|string|true|none||none|
|»» source_outsideport|string|true|none||none|
|»» source_podengine|string|true|none||none|
|»» source_portmode|string|true|none||none|
|»» source_replicasetnum|string|true|none||none|
|»» source_restartpolicy|string|true|none||none|
|»» source_selflabel|string|true|none||none|
|»» source_storagelimits|string|true|none||none|
|»» id|string|true|none||none|
|»» cpcid|string|true|none||none|

## GET 获取集群资源实例配置

GET /dev/cpcc/cpcpodyaml/get_cpcpodyaml.dspy

获取资源实例的配置，普通用户和管理员都是
后续会把实时资源实例看板数据接口和这个进行优化展示，目前先这样吧

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心ID|
|clusterid|query|string| 是 |算力集群ID|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "获取资源实例静态配置成功",
  "data": {
    "total": 1,
    "rows": [
      {
        "id": "evfldtxjkr3jd8zxnfhd5",
        "namespace_name": "4hbm8atruisou2bs24t-n-miwuhbeedm8mwafpiq8ps",
        "serviceaccount_name": "4hbm8atruisou2bs24t-n-miwuhbeedm8mwafpiq8ps-serviceaccount",
        "podcd_name": "evfldtxjkr3jd8zxnfhd5-statefulset",
        "service_name": "evfldtxjkr3jd8zxnfhd5-service",
        "clusterid": "4hBm8atruISOU2bs24t_N",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "source_name": "kyy-new5090gpu-ubuntu2204",
        "source_authuser": "root",
        "source_authpasswd": "kyycloud",
        "source_podengine": "StatefulSet",
        "source_replicasetnum": 1,
        "pod_imagepath": "docker.io/library/ubuntu:22.04",
        "source_memrate": "512Mi",
        "source_cpurate": "1000m",
        "source_selflabel": "app:ubuntu3",
        "source_portmode": "NodePort",
        "source_restartpolicy": "Always",
        "source_apiport": 6035,
        "source_insideport": 3306,
        "source_outsideport": 30063,
        "source_mountpath": "/mnt/data",
        "source_storagelimits": "49Gi",
        "instance_type": "LinuxOS",
        "source_nodeselector": "kyy-gpu=false",
        "username": "kyy-运营",
        "row_num_": 1
      }
    ]
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» rows|[object]|true|none||none|
|»»» id|string|true|none|id|none|
|»»» namespace_name|string|true|none|命名空间|none|
|»»» serviceaccount_name|string|true|none|命名空间服务认证|none|
|»»» podcd_name|string|true|none|资源控制器名称|none|
|»»» service_name|string|true|none|服务名称|none|
|»»» clusterid|string|true|none|集群id|none|
|»»» cpcid|string|true|none|算力中心id|none|
|»»» source_name|string|true|none|资源名称|none|
|»»» source_authuser|string|true|none|初始认证账号|none|
|»»» source_authpasswd|string|true|none|初始认证密码|none|
|»»» source_podengine|string|true|none|资源控制器|none|
|»»» source_replicasetnum|string|true|none|HPA副本数|none|
|»»» pod_imagepath|string|true|none|资源基础镜像|none|
|»»» source_memrate|string|true|none|资源内存限制|none|
|»»» source_cpurate|string|true|none|资源CPU限制|none|
|»»» source_selflabel|string|true|none|资源自身标签|none|
|»»» source_portmode|string|true|none|端口映射模式|none|
|»»» source_restartpolicy|string|true|none|重启策略|none|
|»»» source_apiport|string|true|none|资源内部监听端口|none|
|»»» source_insideport|string|true|none|集群内部映射端口|none|
|»»» source_outsideport|string|true|none|集群外部映射端口|none|
|»»» source_mountpath|string|true|none|容器内挂载点|none|
|»»» source_storagelimits|string|true|none|数据存储大小限制|none|
|»»» instance_type|string|true|none|资源实例类型|none|
|»»» source_nodeselector|string|true|none|节点选择器|none|
|»»» username|string|true|none|所属用户|none|

## POST 更新集群资源实例配置

POST /dev/cpcc/cpcpodyaml/update_cpcpodyaml.dspy

更新资源实例配置，参数类似新增资源实例参数接口传递方式

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心ID|
|clusterid|query|string| 是 |集群唯一标识ID|
|id|query|string| 否 |资源实例配置ID|
|source_name|query|string| 是 |资源实例的名称|
|source_authuser|query|string| 是 |初始认证账号|
|source_authpasswd|query|string| 是 |初始认证密码|
|source_podengine|query|string| 是 |资源实例控制器，下拉框，默认StatefulSet，Deployment，DaemonSet，CronJob，Job，Standalone|
|source_replicasetnum|query|string| 是 |HPA副本数|
|instance_type|query|string| 是 |资源实例类型，下拉框，默认LinuxOS为Linux操作系统，RelationalDB为关系型数据库|
|pod_imagepath|query|string| 是 |基础镜像，下拉框，默认docker.io/library/ubuntu:22.04，docker.io/library/mysql:8.0，docker.io/jupyter/base-notebook:latest|
|source_memrate|query|string| 是 |内存资源限制|
|source_cpurate|query|string| 是 |CPU资源限制|
|source_selflabel|query|string| 是 |自定义标签，用于资源分类|
|source_portmode|query|string| 是 |服务暴露的端口模式，下拉框，默认NodePort，Ingress，LoadBalancer|
|source_restartpolicy|query|string| 是 |容器重启策略，下拉框，默认Always，OnFailure，Never|
|source_apiport|query|string| 是 |服务对外提供的端口|
|source_insideport|query|string| 是 |容器内部监听的端口|
|source_outsideport|query|string| 是 |通过NodePort暴露的节点端口|
|source_mountpath|query|string| 是 |容器内的挂载路径|
|source_storagelimits|query|string| 是 |存储资源限制|
|source_nodeselector|query|string| 否 |节点选择器|
|orgid|query|string| 否 |线下调试/非登录态可指定组织ID进行操作|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "资源参数更新成功,请10秒后查看实时资源实例面板",
  "data": {
    "clusterid": "4hBm8atruISOU2bs24t_N",
    "cpcid": "AROU9udKtPNyh0AZtO_WY",
    "id": "evfldtxjkr3jd8zxnfhd5",
    "instance_type": "LinuxOS",
    "orgid": "mIWUHBeeDM8mwAFPIQ8pS",
    "pod_imagepath": "docker.io/library/ubuntu:22.04",
    "source_apiport": "6035",
    "source_authpasswd": "kyycloud",
    "source_authuser": "root",
    "source_cpurate": "1000m",
    "source_insideport": "3306",
    "source_memrate": "512Mi",
    "source_mountpath": "/mnt/data",
    "source_name": "kyy-new5090gpu-ubuntu2204",
    "source_outsideport": "30063",
    "source_podengine": "StatefulSet",
    "source_portmode": "NodePort",
    "source_replicasetnum": "2",
    "source_restartpolicy": "Always",
    "source_selflabel": "app:ubuntu3",
    "source_nodeselector": "kyy-gpu=false",
    "source_storagelimits": "49Gi"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 删除集群资源实例配置

POST /dev/cpcc/cpcpodyaml/delete_cpcpodyaml.dspy

根据资源实例配置级联删除集群中的相关资源及实例

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|query|string| 是 |要删除的资源实例配置id|
|orgid|query|string| 否 |线下调试/非登录态可指定组织ID进行操作|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "级联删除集群资源成功,请10秒后查看实时资源实例面板",
  "data": {
    "id": "evfldtxjkr3jd8zxnfhd5"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 算力中心新建算力集群（调试中）

POST /dev/cpcc/cpccluster/new_cluster.dspy

重操作约5分钟！！！
Web前端创建算力集群，Web后端接收到参数后传递参数给算力中心服务pcapi。
pcapi进行ssh远程到某算力设备中进行安装算力集群（控制节点），安装结果字段返回给Web后端进行存库。
中间是一连贯操作，请确保Web前后端之间接口有超时判断能力。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心id|
|ctl_nodeid|query|string| 是 |集群控制节点的id|
|cluster_type|query|string| 是 |集群类别，0是kubernetes，1是slurm|
|cluster_name|query|string| 是 |集群名称|
|enable_date|query|string| 是 |启用时间|
|export_date|query|string| 是 |停用时间|

> 返回示例

```json
{
  "status": true,
  "msg": "操作成功!\n加入集群凭证: kubeadm join 192.168.0.3:6443 --token nt80u6.gzpj9dxsrw79270c --discovery-token-ca-cert-hash sha256:7b33439b2a1b37a8d8938513bd45405f57c3255771c3b9b9b90af448d886b0c2",
  "data": {
    "id": "RJZ2GMHSWGVG7iRk_AJYm",
    "node_status": "1",
    "clusterid": "4hBm8atruISOU2bs24t_N",
    "cpcid": "AROU9udKtPNyh0AZtO_WY",
    "role": "master"
  }
}
```

```json
{
  "status": false,
  "msg": "算力中心服务操作失败"
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» id|string|true|none||none|
|»» node_status|string|true|none||none|
|»» clusterid|string|true|none||none|
|»» cpcid|string|true|none||none|
|»» role|string|true|none||none|

## POST 算力中心移除算力集群（未开发）

POST /computing/cpcluster_delete.dspy

重操作约1分钟！！！

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|query|string| 是 |算力集群查找返回的id|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# pcapi_kboss容器云/算力部件(含计价)管理

## POST 新增算力部件

POST /dev/cpcc/cpcwidget/add_cpcwidget.dspy

添加算力部件，其中包含CPU核数，CPU型号，内存用量，GPU个数等信息

注意：
1. 每个算力中心下的算力部件不一样！
2. 添加相同类型和系列的组件，不会新增记录

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心id|
|clusterid|query|string| 是 |算力集群id|
|type|query|string| 是 |算力部件类型（下拉框，cpu/memory/disk/gpu）|
|resource_unit|query|string| 是 |资源分配单位（下拉框，跟随type字段，个cpu/Gi内存/Gi存储/张显卡）|
|unit_price|query|string| 是 |单位单价数额（1.99元每分钟每Mi)|
|model|query|string| 是 |算力部件型号，默认STANDARD|
|stock|query|integer| 是 |库存量，默认为0，显示无货，超过0显示有货|
|charge_unit|query|string| 是 |计费周期（下拉框，默认小时/分钟/秒/天）|
|account_unit|query|string| 是 |计费人民币单位（下拉框，默认元/角/分）|
|add_opt|query|string| 是 |下拉框，是否是增加库存操作,默认给no，可选yes|

> 返回示例

```json
{
  "status": false,
  "msg": "该部件已存在，请前往编辑！"
}
```

```json
{
  "status": true,
  "msg": "新增算力部件成功",
  "data": {
    "account_unit": "元",
    "charge_unit": "小时",
    "cpcid": "AROU9udKtPNyh0AZtO_WY",
    "model": "INTEL(R) XEON(R) PLATINUM 8582C",
    "resource_unit": "m",
    "stock": "0",
    "type": "cpu",
    "unit_price": "1.99",
    "id": "SwaVSlL6RtORQrNTqAGi6",
    "update_time": "2025-06-03 16:24:28"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## GET 获取算力部件

GET /dev/cpcc/cpcwidget/get_cpcwidget.dspy

展示该算力中心下所有的算力部件

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心id|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "获取算力部件成功",
  "data": {
    "total": 14,
    "rows": [
      {
        "id": "SwaVSlL6RtORQrNTqAGi6",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "cpu",
        "model": "INTEL(R) XEON(R) PLATINUM 8582C",
        "unit_price": 1.5,
        "resource_unit": "核",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:56",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "OmME0B0AQjCkr__TT2LSZ",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "cpu",
        "model": "STANDARD",
        "unit_price": 2.2,
        "resource_unit": "核",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:53",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "e6FGUkiEN6uujVfNp6oBK",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "cpu",
        "model": "AMD EPYC 7542 32-Core Processor",
        "unit_price": 0.8,
        "resource_unit": "核",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:50",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "meebE6wMvHi0eLHw-GGkJ",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "disk",
        "model": "DATA",
        "unit_price": 0.01,
        "resource_unit": "Gi",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:54",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "JFaQH-YjuYjfX7oy7lojF",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "disk",
        "model": "SYS",
        "unit_price": 0.005,
        "resource_unit": "Gi",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:51",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "XXXe35qAC1E0Dqu2GN5pN",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "gpu",
        "model": "STANDARD-8G",
        "unit_price": 2,
        "resource_unit": "卡",
        "stock": 5,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 16:29:22",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_X",
            "clustername": "通州区",
            "stock": 2,
            "consumed": 0
          },
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 3,
            "consumed": 0
          }
        ]
      },
      {
        "id": "Rj-YyF__ELLvosq6Mgxjn",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "gpu",
        "model": "A100-80G",
        "unit_price": 18,
        "resource_unit": "卡",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:55",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "ImmA3ghOcrQ-Ltebmm1x2",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "gpu",
        "model": "RTX5090-32G",
        "unit_price": 6,
        "resource_unit": "卡",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:51",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "BCEJAaX7pt20bfni4hJbp",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "gpu",
        "model": "RTX4090-24G",
        "unit_price": 4,
        "resource_unit": "卡",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:48",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "aHUd2O5sawlVqsn2icysS",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "gpu",
        "model": "V100-32G",
        "unit_price": 12,
        "resource_unit": "卡",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:47",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "uSOsd4iM5ohtDvJPMqE-h",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "memory",
        "model": "Samsung DDR4 DIMMs",
        "unit_price": 0.005,
        "resource_unit": "Gi",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:57",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "PC9YvPO3pJ_I1_fd8xvca",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "memory",
        "model": "STANDARD",
        "unit_price": 0.0004,
        "resource_unit": "Gi",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:55",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "LLHswyKb78yYPMZIDBbjd",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "memory",
        "model": "Crucial P-series",
        "unit_price": 0.0005,
        "resource_unit": "Gi",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:52",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      },
      {
        "id": "B2Jl1_6P7mMdIdtvO-Qcf",
        "cpcid": "AROU9udKtPNyh0AZtO_WY",
        "type": "memory",
        "model": "Kingston FURY",
        "unit_price": 0.0002,
        "resource_unit": "Gi",
        "stock": 0,
        "consumed": 0,
        "charge_unit": "小时",
        "account_unit": "元",
        "update_time": "2025-06-10 15:22:47",
        "import_export": [
          {
            "clusterid": "4hBm8atruISOU2bs24t_N",
            "clustername": "朝阳区",
            "stock": 0,
            "consumed": 0
          }
        ]
      }
    ]
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total|integer|true|none||none|
|»» rows|[object]|true|none||none|
|»»» id|string|true|none||none|
|»»» cpcid|string|true|none||算力中心ID|
|»»» type|string|true|none||算力部件类型，目前只有cpu/memory/disk/gpu四种固定类型|
|»»» model|string|true|none||部件型号/系列|
|»»» unit_price|number|true|none||单位单价数额（2.5元/Mi*小时)|
|»»» resource_unit|string|true|none||计费资源单位（个核/Mi内存/Gi存储/块gpu）|
|»»» stock|integer|true|none||总库存数|
|»»» consumed|integer|true|none||总消耗数|
|»»» charge_unit|string|true|none||计费周期单位（小时/分钟/秒/天）|
|»»» account_unit|string|true|none||计费货币单位（元/角/分）|
|»»» update_time|string|true|none||更新时间|
|»»» import_export|[object]|true|none||库存元数据|
|»»»» clusterid|string|true|none||集群名|
|»»»» clustername|string|true|none||集群id|
|»»»» stock|integer|true|none||库存数|
|»»»» consumed|integer|true|none||消耗数|
|»»» clusterid|string|true|none||算力集群ID|
|»»» row_num_|integer|true|none||none|

## GET 部件组合询价

GET /dev/cpcc/cpcwidget/accrual_price.dspy

客户端通过此接口，查询不同算力部件组合后的产品定价

如用户要查询某些部件组合运行2天的定价，可以传参数（下面参数说明不支持array友好显示，array里面每项都是字典/json，看这里就行，amount字段值是 整型）：
{
        "resources": [
            {"type": "cpu", "model": "INTEL(R) XEON(R) PLATINUM 8582C", "amount": 4},
            {"type": "memory", "model": "Samsung DDR4 DIMMs", "amount": 8192},  # 8GB必须转成8192Mi
            {"type": "disk", "model": "DATA", "amount": 512},
            {"type": "gpu", "model": "RTX5090-32G", "amount": 2}
        ],
        "duration": 2,
        "duration_unit": "天"
    }
进行计算，其他条件同理

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心id|
|resources|query|array[string]| 是 |1. 多种算力部件自由组合成的数组；|
|duration|query|integer| 是 |使用时长，整数|
|duration_unit|query|string| 是 |使用时长单位，可以是小时，天，周，月|
|clusterid|query|string| 否 |集群id，查看集群库存|

#### 详细说明

**resources**: 1. 多种算力部件自由组合成的数组；
2. 内存一定是以Mi为单位（如8GB必须转成8192Mi），其他单位要提前转成Mi级；
3.字段解释：
type: 部件类型，下拉cpu，memory，disk，gpu
model：部件子类型，自定义填写
amount：部件使用量，整型，输入框后面显示单位（cpu-核，memory-Mi，disk-Gi，gpu-卡）

> 返回示例

```json
{
  "status": true,
  "msg": "获取部件组合价格成功",
  "data": {
    "total_price": 64.08,
    "currency": "元",
    "price_details": [
      {
        "resource_name": "cpu INTEL(R) XEON(R) PLATINUM 8582C",
        "resource_type": "cpu",
        "amount": 4,
        "resource_unit": "核",
        "unit_price": 1.5,
        "duration": "1",
        "duration_unit": "小时",
        "subtotal": 6
      },
      {
        "resource_name": "memory Samsung DDR4 DIMMs",
        "resource_type": "memory",
        "amount": 8192,
        "resource_unit": "Mi",
        "unit_price": 0.005,
        "duration": "1",
        "duration_unit": "小时",
        "subtotal": 40.96
      },
      {
        "resource_name": "disk DATA",
        "resource_type": "disk",
        "amount": 512,
        "resource_unit": "Gi",
        "unit_price": 0.01,
        "duration": "1",
        "duration_unit": "小时",
        "subtotal": 5.12
      },
      {
        "resource_name": "gpu RTX5090-32G",
        "resource_type": "gpu",
        "amount": 2,
        "resource_unit": "卡",
        "unit_price": 6,
        "duration": "1",
        "duration_unit": "小时",
        "subtotal": 12
      }
    ],
    "status": true,
    "message": "汇算正常",
    "duration": "1",
    "duration_unit": "小时"
  }
}
```

```json
{
  "status": false,
  "msg": "无效的 gpu 部件型号: RTXs5090-32G",
  "data": {
    "total_price": 52.08,
    "currency": "元",
    "price_details": [
      {
        "resource_name": "cpu INTEL(R) XEON(R) PLATINUM 8582C",
        "resource_type": "cpu",
        "amount": 4,
        "resource_unit": "核",
        "unit_price": 1.5,
        "duration": "1",
        "duration_unit": "小时",
        "subtotal": 6
      },
      {
        "resource_name": "memory Samsung DDR4 DIMMs",
        "resource_type": "memory",
        "amount": 8192,
        "resource_unit": "Mi",
        "unit_price": 0.005,
        "duration": "1",
        "duration_unit": "小时",
        "subtotal": 40.96
      },
      {
        "resource_name": "disk DATA",
        "resource_type": "disk",
        "amount": 512,
        "resource_unit": "Gi",
        "unit_price": 0.01,
        "duration": "1",
        "duration_unit": "小时",
        "subtotal": 5.12
      },
      {
        "resource_type": "gpu",
        "error": "无效的 gpu 部件型号: RTXs5090-32G"
      }
    ],
    "status": false,
    "message": "无效的 gpu 部件型号: RTXs5090-32G",
    "duration": "1",
    "duration_unit": "小时"
  }
}
```

```json
{
  "status": false,
  "msg": "memory Samsung DDR4 DIMMs 库存不足 (库存: 1280, 请求: 8192)",
  "data": {
    "total_price": 23.12,
    "currency": "元",
    "price_details": [
      {
        "resource_name": "cpu INTEL(R) XEON(R) PLATINUM 8582C",
        "resource_type": "cpu",
        "amount": 4,
        "resource_unit": "核",
        "unit_price": 1.5,
        "duration": "1",
        "duration_unit": "小时",
        "subtotal": 6
      },
      {
        "resource_type": "memory",
        "error": "memory Samsung DDR4 DIMMs 库存不足 (库存: 1280, 请求: 8192)"
      },
      {
        "resource_name": "disk DATA",
        "resource_type": "disk",
        "amount": 512,
        "resource_unit": "Gi",
        "unit_price": 0.01,
        "duration": "1",
        "duration_unit": "小时",
        "subtotal": 5.12
      },
      {
        "resource_name": "gpu RTX5090-32G",
        "resource_type": "gpu",
        "amount": 2,
        "resource_unit": "卡",
        "unit_price": 6,
        "duration": "1",
        "duration_unit": "小时",
        "subtotal": 12
      }
    ],
    "status": false,
    "message": "memory Samsung DDR4 DIMMs 库存不足 (库存: 1280, 请求: 8192)",
    "duration": "1",
    "duration_unit": "小时"
  }
}
```

```json
{
  "status": false,
  "msg": "没有该类型组件",
  "data": {
    "total_price": 0,
    "currency": "元",
    "price_details": [
      {
        "resource_type": "cpu",
        "error": "没有该类型组件"
      },
      {
        "resource_type": "memory",
        "error": "没有该类型组件"
      },
      {
        "resource_type": "disk",
        "error": "没有该类型组件"
      },
      {
        "resource_type": "gpu",
        "error": "没有该类型组件"
      }
    ],
    "status": false,
    "message": "没有该类型组件",
    "duration": 1,
    "duration_unit": "小时"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» total_price|number|true|none||none|
|»» currency|string|true|none||none|
|»» price_details|[object]|true|none||none|
|»»» resource_name|string|true|none||none|
|»»» resource_type|string|true|none||none|
|»»» amount|integer|true|none||none|
|»»» resource_unit|string|true|none||none|
|»»» unit_price|number|true|none||none|
|»»» duration|string|true|none||none|
|»»» duration_unit|string|true|none||none|
|»»» subtotal|integer|true|none||none|
|»» status|boolean|true|none|接口状态|none|
|»» message|string|true|none|接口信息|none|
|»» duration|string|true|none|时间间隔长度|2|
|»» duration_unit|string|true|none|时间间隔单位|小时/天/周/月|

## POST 更新算力部件单价

POST /dev/cpcc/cpcwidget/update_cpcwidget.dspy

更新算力部件信息

注意：
1.只能更新单位单价!
2.必须登录态才能操作！

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|query|string| 否 |获取算力部件得到的id|
|cpcid|query|string| 是 |算力中心id|
|unit_price|query|string| 是 |更新单位单价，浮点数，apifox不支持设置浮点格式，请注意|
|type|query|string| 是 |算力部件类型|
|model|query|string| 是 |gpu型号系列|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "更新算力部件成功",
  "data": {
    "cpcid": "AROU9udKtPNyh0AZtO_WY",
    "id": "YnTYUrOhKTB_WjuK8zNj5",
    "unit_price": "0.0009"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 移除算力部件

POST /dev/cpcc/cpcwidget/delete_cpcwidget.dspy

移除算力中心部件

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|query|string| 是 |节点部件查找返回的id|
|cpcid|query|string| 是 |算力中心id|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# pcapi_kboss容器云/算力集群节点管理(未开发)

## POST 算力集群新增工作节点（调试中）

POST /dev/cpcc/cpcworker/new_cpcworker.dspy

重操作约3分钟！！！
Web前端给某集群新增算力节点，Web后端接收到参数后传递参数给算力中心服务pcapi。
pcapi进行ssh远程到某算力设备中进行安装算力集群（控制节点），安装结果字段返回给Web后端进行存库。
中间是一连贯操作，请确保Web前后端之间接口有超时判断能力。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心id|
|clusterid|query|string| 是 |选中集群id|
|worker_nodeid|query|string| 是 |选中算力设备id|

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

## POST 算力集群移除工作节点（未开发）

POST /

重操作约1分钟！！！

> 返回示例

> 200 Response

```json
{}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

# pcapi_kboss容器云/购买页通用接口(调试中)

## GET 获取站点GPU资源配置库存

GET /dev/cpcc/cpcwidget/obtaining_gpuinfo.dspy

购买页GPU算力资源（含库存信息）
获取去重后显示该算力中心下的GPU算力资源
以算力集群为最小单位获取资源

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 否 |算力中心id|
|clusterid|query|string| 否 |算力集群id|

> 返回示例

```json
{
  "status": true,
  "msg": "获取集群GPU库存成功",
  "data": {
    "V100-32G": 8,
    "RTX4090-24G": 12,
    "RTX5090-32G": 10,
    "A100-80G": 5,
    "STANDARD-8G": 1
  }
}
```

```json
{
  "status": true,
  "msg": "获取集群GPU库存成功",
  "data": {
    "V100-32G": 8,
    "RTX4090-24G": 12,
    "RTX5090-32G": 10,
    "另一个算力集群(不同算力中心下)显卡型号XXX-12G": 1,
    "A100-80G": 5,
    "STANDARD-8G": 1
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» V100-32G|integer|true|none||none|
|»» RTX4090-24G|integer|true|none||none|
|»» RTX5090-32G|integer|true|none||none|
|»» A100-80G|integer|true|none||none|
|»» STANDARD-8G|integer|true|none||none|

## GET 获取站点不可部署产品ID

GET /dev/cpcc/cpcbuy/determine_accommodat.dspy

1. 判断购买页的产品组合是否能完整部署到某站点/集群中的可用节点上？
2. 原理：资源实例是运行在某节点上的，至少有一个工作节点拥有用户勾选的所有部件库存可用量时才可进行下一步，否则报无可用节点！
3. 入参：算力中心-集群中若干算力部件参数组组成的JSON
4. 出参：置灰/不可部署产品id组成的数组

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|cpcid|query|string| 是 |算力中心id|
|clusterid|query|string| 是 |集群id|
|resources|query|string| 是 |请求资源详情|
|kyylabels|query|string| 是 |none|

> 返回示例

> 200 Response

```json
{
  "status": true,
  "msg": "获取不可部署产品ID成功",
  "data": [
    "5436-f-gdsb--ewrewrerrtwt",
    "6787jhgvgjhv32412343142jvgj"
  ],
  "reason": "dynamic"
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» status|boolean|true|none||接口状态|
|» msg|string|true|none||接口状态详情|
|» data|[string]|true|none||none|
|» reason|string|true|none||判定环节|

# 数据模型

