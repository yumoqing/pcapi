import paramiko


def exec_command(command):
    # 设置SSH连接参数
    hostname = '10.8.64.15'
    port = 22  # SSH端口,默认是22
    username = 'ceni'
    password = '1qazXSW@34'

    # hostname = '127.0.0.1'
    # port = 722  # SSH端口,默认是22
    # username = 'ceni'
    # password = '1qazXSW@34'

    # 创建SSH客户端
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password)

    # 执行命令
    stdin, stdout, stderr = client.exec_command(command)
    result_out=stdout.read().decode("utf-8")
    result_error=stderr.read().decode("utf-8")

    result={
        "stdout": result_out,
        "stderr": result_error
    }
    # 关闭连接
    # 关闭连接
    client.close()

    return result

def exec_command_hostname(command,hostname,port,username,password):
    # 创建SSH客户端
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password)

    # 执行命令
    stdin, stdout, stderr = client.exec_command(command)
    result_out=stdout.read().decode("utf-8")
    result_error=stderr.read().decode("utf-8")

    result={
        "stdout": result_out,
        "stderr": result_error
    }
    # 关闭连接
    # 关闭连接
    client.close()

    return result