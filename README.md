# S3-UI

Приложение для просмотра списка объектов в s3 бакете и формирования временных ссылок для скачивания

#### переменные окружения:
- YC_BUCKET_NAME - название бакета
- YC_ACCESS_KEY и YC_SECRET_ACCESS_KEY - ключи сервис аккаунта для доступа к бакету
- URL_EXPIRES - время жизни временной ссылки в секундах
- KEY_PREFIXES - необходимо для ограничения вывода списка объектов, передается через запятую, напр. "mysql,express"
- LDAP_SERVER - LDAP сервер для авторизации, напр. ldap://office.lamoda.ru
- LDAP_BASE_DN - Базовый DN для поиска групп и пользователя напр. "DC=office,DC=lamoda,DC=ru
- LDAP_SERVICE_ACCOUNT_NAME - имя сервис аккаунта от которого просиходит поиск в ldap
- LDAP_SERVICE_ACCOUNT_PASSWORD - пароль от сервис аккаунта {LDAP_SERVICE_ACCOUNT_NAME}
