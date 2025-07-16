from ldap3 import Server, Connection, ALL, NTLM, SUBTREE,MODIFY_REPLACE
import json




# LDAP服务器信息
# ldap_server_uri = 'ldap://127.0.0.1:7389'  # 或者 ldaps://your-ldap-server-secure
ldap_server_uri = 'ldap://10.8.64.15'  # 或者 ldaps://your-ldap-server-secure
ldap_user = 'cn=admin,dc=test,dc=com'
ldap_password = '123456'
ldap_base = 'dc=test,dc=com'

# 创建LDAP服务器对象
server = Server(ldap_server_uri, get_info=ALL)
# 创建连接对象并绑定用户
conn = Connection(server, user=ldap_user, password=ldap_password, auto_bind=True)


def  get_all_ldap_user():
    # 搜索条目
    search_filter = '(objectClass=person)'
    search_attribute = ['cn', 'sn', 'mail']
    conn.search(search_base=ldap_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=search_attribute)
    result=[ json.loads(x.entry_to_json())for x in conn.entries]
    return result
def  get_all_ldap_cn():
    # 搜索条目
    search_filter = '(objectClass=posixGroup)'
    search_attribute = ['cn', 'objectClass', 'gidNumber']
    conn.search(search_base=ldap_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=search_attribute)

    result=[ json.loads(x.entry_to_json())for x in conn.entries]
    return result
def  get_one_cn(cn):
    # 搜索条目
    search_filter = f'(&(cn={cn})(objectClass=posixGroup))'
    search_attribute = ['cn', 'objectClass', 'gidNumber']

    conn.search(search_base=ldap_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=search_attribute
                )
    if conn.entries is None:
        return None
    else:
        return     json.loads(conn.entries[0].entry_to_json())


''''
传参示例
    # uid="test_add1"
    # plaintext_password="654321"
    # uid_number=123456
    # cn="test"
    # add_ldap_user(uid,plaintext_password,cn)
'''
def  add_ldap_user(uid,uid_number,plaintext_password,cn ):

    cn_attr=get_one_cn(cn)
    new_user_dn=f"uid={uid},ou=test,{ldap_base}"
    new_user_attrs={
    "objectClass": ["top", "posixAccount", "inetOrgPerson", "shadowAccount"],
    "uidNumber":uid_number,
    "gidNumber":cn_attr["attributes"]["gidNumber"],
    'sn':[uid],
    'loginShell': ["/bin/bash"],
    'homeDirectory':["/srv/nfs/"+uid],
    'cn':[cn]
    }

    flag=conn.add(new_user_dn,new_user_attrs["objectClass"],new_user_attrs)
    print(conn.result)
    if flag is True:
        return  modify_password(new_user_dn, plaintext_password)
    else:
        return conn.result


def modify_password(new_user_dn,plaintext_password):
    mod_attrs = {
        'userPassword': (
            MODIFY_REPLACE,[plaintext_password])
    }
    conn.modify(new_user_dn, mod_attrs)
    return conn.result

def delete_ldap_user(uid):

    user_dn=f"uid={uid},ou=test,{ldap_base}"

    conn.delete(user_dn)
    return conn.result
