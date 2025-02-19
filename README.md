# S3-UI

Приложение для просмотра списка объектов в s3 бакете и формирования временных ссылок для скачивания

#### переменные окружения:
- YC_BUCKET_NAME - название бакета
- YC_ACCESS_KEY и YC_SECRET_ACCESS_KEY - ключи сервис аккаунта для доступа к бакету
- URL_EXPIRES - время жизни временной ссылки в секундах
- KEY_PREFIXES - необходимо для ограничения вывода списка объектов, передается через запятую, напр. "mysql,express"
- LDAP_SERVER - LDAP сервер для авторизации, напр. ldap://office.lamoda.ru
- LDAP_BASE_DN - Базовый DN для поиска групп и пользователя напр. "DC=office,DC=lamoda,DC=ru
- LDAP_SERVICE_ACCOUNT_NAME - имя сервис аккаунта от которого просиходит поиск в LDAP
- LDAP_SERVICE_ACCOUNT_PASSWORD - пароль от сервис аккаунта {LDAP_SERVICE_ACCOUNT_NAME}

Префикс поиска объектов в s3 привязан к значению KEY_PREFIXES и группам в LDAP: g_s3_ui_<название сервиса>_ro.
```
если
KEY_PREFIXES="mysql,pgsql"
а группа в которую добавлен пользователь называется g_s3_ui_express_ro
значит поиск будет происходить по двум префиксам - "mysql/express" и "pgsql/express" и s3-ui покажет соответствующие объекты, при условии что они есть в s3.
Если пользователь добавлен в несколько групп, предположим еще в g_s3_ui_adv_ro, то поиск будет осуществлен по 4-м префиксам:

- mysql/express
- pgsql/express
- mysql/adv
- pgsql/adv
```