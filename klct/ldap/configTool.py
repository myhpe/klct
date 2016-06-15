import os
import ssl
import subprocess
import socket
import sys
import ldap3
import ConfigParser
from ldap3 import Server, Connection, ALL


def check_valid_IP(host_name):
    """Checks if the given hostName is a valid IP address.
    Return 1 if valid, 0 if invalid.
    note: only checks for valid ipv4 IPs
          need to implement validation for IPV6
    """
    try:
        host_name = socket.gethostbyname(host_name)
        try:
            socket.inet_aton(host_name)
            return 1
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, host_name)
                return 1
            except OSError:
                return 0
    except socket.gaierror:
        try:
            socket.inet_pton(socket.AF_INET6, host_name)
            return 1
        except socket.error:
            return 0


def setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path):
    """Sets up a connection given the parameters.
    Note: unbind the returned connection when finished using socket
    """
    return_values = {'exit_status':0, 'message':[], 'error':[], 'server':[], 'conn':[]}
    if port_number is None and want_tls=='n':
        port_number = 389
    elif port_number is None and want_tls=='y':
        port_number = 636
    try:
        if want_tls == 'n':
            return_values['server'] = Server(host_name, port=port_number, get_info=ALL)
        else:
            tls_object = ldap3.Tls(ca_certs_file=tls_cert_path, validate=ssl.CERT_REQUIRED)
            return_values['server'] = Server(host_name, port=port_number, use_ssl=True, tls=tls_object, get_info=ALL)
        #print("\nTrying to connect...")
        #print(server)
        return_values['conn'] = Connection(return_values['server'], version=3, user=user_name, password=password, auto_bind=True)
        #print("connection started")
        #conn.open() #bind implies open
        #if not conn.bind():
        #    return 0, "bind failed", conn.results
        if want_tls == 'y':
            #print("starting tls\n")
            #conn.open()
            conn.start_tls()
        #print(conn)
        return_values['exit_status'] = 1
        return_values['message'] = "Successfully connected"
    except ldap3.LDAPSocketOpenError as err:
        return_values['message'] = "Failed to connect due to invalid socket."
        return_values['error'] = err
    except ldap3.LDAPInvalidPortError as err:
        return_values['message'] = "Invalid Port"
        return_values['error'] = err
    except AttributeError as err:
        return_values['message'] = "Invalid log in info"
        return_values['error'] = err
    except ldap3.LDAPPasswordIsMandatoryError as err:
        return_values['message'] = "Please enter a password"
        return_values['error'] = err
    except:
        return_values['message'] = "Failed to connect due to unknown reasons"
        return_values['error'] = sys.exc_info()[1]
    return return_values

def ping_LDAP_server(host_name):
    """Checks if the given hostName is valid, and pings it.
    """
    is_valid = check_valid_IP(host_name)
    if not is_valid:
        return -1
    response = None
    with open(os.devnull, "w"):
        try:
            subprocess.check_output(["ping", "-c", "1", host_name], stderr=subprocess.STDOUT, universal_newlines=True)
            response = 1
        except subprocess.CalledProcessError:
            response = 0
    return response


def connect_LDAP_server_basic(host_name, port_number):
    """Attempts to connect to the provided hostName and port number, default port is 389 if none provided.
    """
    conn_info = setup_connection(host_name, port_number, "", "", 'n', "")
    if conn_info['exit_status'] == 1:
        conn_info['conn'].unbind()
    return conn_info


def connect_LDAP_server(host_name, port_number, user_name, password, want_tls, tls_cert_path):
    """Attempts to connect to the provided hostName and port number, default port is 389 if none provided, using the provided user name and pass.
    Note: tls not working
    """
    conn_info = setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path)
    if conn_info['exit_status'] == 1:
        conn_info['conn'].unbind()
    return conn_info


def retrieve_server_info(server):
    """Retrieves the information related to the server passed in
    """
    dict = {'info':server.info, 'schema':server.schema}
    return dict


#def check_LDAP_suffix(conn, base_dn):
    #for entry in dc_list:
    #    check if each entry in dc_list is in one of the suffixes in the ldapserver entries


def list_user_related_OC():
    print("needs to be implemented")


def list_users(conn, limit):
    print("needs to be implemented")
    if limit == None:
        limit = 3
    conn.search(search_base='', search_filter='(objectClass=users)', search_scope=ldap3.SUBTREE, attributes=['cn','user'], paged_size=limit)


def get_user(conn, name):
    #conn.search(search_base='dc=cdl,dc=hp,dc=com', search_filter ='(ou='+name+')', search_scope=ldap3.SUBTREE, attributes=['title'], paged_size=5)
    #conn.search('dc=cdl,dc=hp,dc=com', '(givenName='+name+')')
    conn.search('dc=cdl,dc=hp,dc=com', '(ou='+name+')', attributes=['sn','krbLastPwdChange','objectclass'])
    print(conn.entries)
    #for entry in conn.response:
    #    print(entry['dn'], entry['attributes'])


def list_group_related_OC():
    print("needs to be implemented")


def list_groups():
    print("needs to be implemented")


def get_group():
    print("needs to be implemented")


def show_config():
    print("needs to be implemented")


def save_config():
    print("needs to be implemented")
 
