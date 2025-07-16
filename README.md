# pcapi
算力中心API服务器

## 安装须知
* 先执行sh install.sh安装升级第三方库
* 将sqlor,ahserver,apppublic,rbac,appbase库拉取下来依次安装
* 建议不要直接pip install -r requirement.txt,小麻烦较多

## 安全保证

* 使用https协议
* 使用BasicAuth传输用户密码
* 检查IP是否在允许IP集中
* 上述检查失败的请求全部返回401

## 服务方代码

### 例子功能

#### 步骤1 包装K8S功能
```
async def create_namespaced_job_v1(namespace, jobdesc):
    batch_v1 = client.BatchV1Api()
    f = awaitify(batch_v1.create_namespaced_job)
    return await f(namespace=namespace, body=jobdesc)
```
上述代码用来包装k8s的以下功能
```
batch_v1 = client.BatchV1Api()
batch_v1.create_namespaced_job(namespace=..., nody=...)
```
#### 步骤2 让新功能在dspy脚本中可用
将下面的代码放在def init_func()函数的最后：
```
g.create_namespaced_job_v1 = create_namespaced_job_v1
```
### 功能扩充
有新功能需要扩充时,请参照上述功能操作

### 数据参数话函数
paramify(data, ns):
data是一个python的字符串,字典或数组,其中的数据有用“${name}$"形式定义的变量,此函数将data中的参数用ns字典中的值替换
此函数在dspy脚本中可用

### 后台目录协议
* 所有后台程序在wwwroot下
* wwwroot中只有一个api目录
* api目录按照api的版本创建v{版本号}目录, 版本号为整数,从“1”开始
* 每个api一个在版本目录下创建一个api名称的目录
* api代码在api名称目录的index.dspy文件中

### 接口脚本例子
```
info('test .....{params_kw=}')

data = {
	"k":"${key}$",
	"s":"${secretkey}$"
}
ns = paramify(data, params_kw)
return ns
```

## 请求方代码例子

### curl版本

curl --basic --user kyycloud:Kyy@123456 https://pcapi.opencomputing.cn

### dspy版本
```
# 客户方需要提供用户密码,用basic_auth_headers函数生成验证用户所需
# 的http请求的headers,并在请求是放在headers参数中
headers = basic_auth_headers('kyycloud','Kyy@123456')
hc = HttpClient()
resp = await hc.request('https://pcapi.opencomputing.cn',
            method='GET',
            params={
                "a":"1",
                "key":"87y32iuhi453u8y56",
                "secretkey":"qqqqqcccccceeeee"
            },
            headers=headers)
info(f'{resp=}')
return resp




# bricks