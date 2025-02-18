from ldap3 import Server, Connection, ALL, SUBTREE
import os, sys
from loguru import logger

try:
    LDAP_SERVER = os.environ['LDAP_SERVER']
    LDAP_BASE_DN = os.environ['LDAP_BASE_DN']
    LDAP_GROUP_NAME = os.environ['LDAP_GROUP_NAME']
    LDAP_SERVICE_ACCOUNT_NAME = os.environ['LDAP_SERVICE_ACCOUNT_NAME']
    LDAP_SERVICE_ACCOUNT_PASSWORD = os.environ['LDAP_SERVICE_ACCOUNT_PASSWORD']
except KeyError as e:
    logger.error("env not set: {}", e)
    sys.exit(1)

LDAP_USER_DN = 'OU=Offices,' + LDAP_BASE_DN
LDAP_GROUP_DN = 'OU=Groups,' + LDAP_BASE_DN

LDAP_SERVICE_ACCOUNT_DN = f'CN={LDAP_SERVICE_ACCOUNT_NAME},OU=Service Accounts,' + LDAP_BASE_DN

def ldap_authenticate(username, password):
    try:
        server = Server(LDAP_SERVER, get_info=ALL)
        service_conn = Connection(server, user=LDAP_SERVICE_ACCOUNT_DN, password=LDAP_SERVICE_ACCOUNT_PASSWORD)
        
        if not service_conn.bind():
            logger.error("Failed to bind with service account")
            return False

        user_search_filter = f'(sAMAccountName={username})'
        service_conn.search(LDAP_USER_DN, user_search_filter, attributes=['cn', 'memberOf'])

        member_of = service_conn.entries[0].memberOf
        filtered_member_of = [group for group in member_of if group.startswith('CN=g_s3_ui_')]
        
        prefix = 'CN=g_s3_ui_'
        suffix = f'_ro,OU=Rights Assignment,{LDAP_GROUP_DN}'

        projects = [item.removeprefix(prefix).removesuffix(suffix) for item in filtered_member_of]

        if not service_conn.entries:
            logger.error("User not found")
            return False

        user_dn = service_conn.entries[0].entry_dn

        user_conn = Connection(server, user=user_dn, password=password)
        if not user_conn.bind():
            logger.error("User authentication failed")
            return False

        return projects

    except Exception as e:
        logger.error(f"LDAP Error: {e}")
        return False
