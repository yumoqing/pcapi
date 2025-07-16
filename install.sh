#!/bin/bash
pip3 -V
pip3 list
pip3 install kubernetes packaging ldap3 paramiko python-dateutil aiohttp-socks asyncssh nanoid redis -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install --upgrade cryptography pyOpenSSL
