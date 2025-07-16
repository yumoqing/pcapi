# Authentication

- HTTP Authentication, scheme: basic

# ldap相关

## GET 获取全部ldapUser

GET /api/v1/ldap/get_all_ldap_user

> 返回示例

> 200 Response

```json
{
    "status": "success",
    "data": [
        {
            "attributes": {
                "cn": [
                    "test1"
                ],
                "mail": [],
                "sn": [
                    "test1"
                ]
            },
            "dn": "uid=test1,ou=test,dc=test,dc=com"
        },
        {
            "attributes": {
                "cn": [
                    "test"
                ],
                "mail": [],
                "sn": [
                    "test_add2"
                ]
            },
            "dn": "uid=test_add2,ou=test,dc=test,dc=com"
        }
    ]
}
```

### 返回结果

| 状态码 | 状态码含义                                                   | 说明   | 数据模型   |
| --- | ------------------------------------------------------- | ---- | ------ |
| 200 | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | none | Inline |

## GET 删除某个LdapUser

GET /api/v1/ldap/delete_ldap_user

### 请求参数

| 名称  | 位置    | 类型     | 必选  | 说明   |
| --- | ----- | ------ | --- | ---- |
| uid | query | string | 否   | none |

> 返回示例

> 200 Response

```json
{
    "status": "success",
    "data":{
        "result": 0,
        "description": "success",
        "dn": "",
        "message": "",
        "referrals": null,
        "type": "delResponse"
        }

}
```

### 返回结果

| 状态码 | 状态码含义                                                   | 说明   | 数据模型   |
| --- | ------------------------------------------------------- | ---- | ------ |
| 200 | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | none | Inline |

### 

## GET 获取某个CN

GET /api/v1/ldap/get_one_cn

### 请求参数

| 名称  | 位置    | 类型     | 必选  | 说明   |
| --- | ----- | ------ | --- | ---- |
| cn  | query | string | 否   | none |

> 返回示例

> 200 Response

```json
{
    "status": "success",
    "data":{
        "attributes": {
            "cn": [
                "test"
            ],
            "gidNumber": [
                47758
            ],
            "objectClass": [
                "posixGroup",
                "top"
            ]
        },
        "dn": "cn=test,ou=test,dc=test,dc=com"
    }
}
```

### 返回结果

| 状态码 | 状态码含义                                                   | 说明   | 数据模型   |
| --- | ------------------------------------------------------- | ---- | ------ |
| 200 | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | none | Inline |

### 

## GET 新增某个LdapUser

GET /api/v1/ldap/add_ldap_user

### 请求参数

| 名称                 | 位置    | 类型     | 必选  | 说明     |
| ------------------ | ----- | ------ | --- | ------ |
| uid                | query | string | 否   | 集群账号   |
| uid_number         | query | string | 否   | 集群账号id |
| plaintext_password | query | string | 否   | 密码     |
| cn                 | query | string | 否   | none   |

> 返回示例

> 200 Response

```json
{
    "status": "success",
    "data":{
        "result": 0,
        "description": "success",
        "dn": "",
        "message": "",
        "referrals": null,
        "type": "modifyResponse"

    }
}
```

### 返回结果

| 状态码 | 状态码含义                                                   | 说明   | 数据模型   |
| --- | ------------------------------------------------------- | ---- | ------ |
| 200 | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | none | Inline |

### 

## GET 获取全部ldapCN

GET /api/v1/ldap/get_all_ldap_cn

> 返回示例

> 200 Response

```json
{
    "status": "success",
    "data": [
        {
            "attributes": {
                "cn": [
                    "testGroup"
                ],
                "gidNumber": [
                    34423
                ],
                "objectClass": [
                    "posixGroup",
                    "top"
                ]
            },
            "dn": "cn=testGroup,ou=test,dc=test,dc=com"
        },
        {
            "attributes": {
                "cn": [
                    "test"
                ],
                "gidNumber": [
                    47758
                ],
                "objectClass": [
                    "posixGroup",
                    "top"
                ]
            },
            "dn": "cn=test,ou=test,dc=test,dc=com"
        }
    ]
}
```

### 返回结果

| 状态码 | 状态码含义                                                   | 说明   | 数据模型   |
| --- | ------------------------------------------------------- | ---- | ------ |
| 200 | [OK](https://tools.ietf.org/html/rfc7231#section-6.3.1) | none | Inline |
