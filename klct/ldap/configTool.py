import os
import ssl
import subprocess
import socket
import sys
import ldap3
from ldap3 import Server, Connection, ALL
import yaml


def check_valid_IP(host_name):
    """
    Checks if the given hostName is a valid IP address.
    Return 1 if valid, 0 if invalid.
    """
    try:
        socket.inet_aton(host_name)
        return 1
    except socket.error:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host_name)
        return 1
    except socket.error:
        return 0


def setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path):
    """
    Sets up a connection given the parameters.
    Note: unbind the returned connection when finished using socket
    Note: need to find a way to check validation of certificate, eg. expiration, etc
    """
    return_values = {'exit_status': 0, 'message': [], 'error': [], 'server': [], 'conn': []}
    if port_number is None and want_tls == 'n':
        port_number = 389
    elif port_number is None and want_tls == 'y':
        port_number = 636
    try:
        if want_tls == 'n':
            return_values['server'] = Server(host_name, port=port_number, get_info=ALL)
        else:
            tls_object = ldap3.Tls(ca_certs_file=tls_cert_path, validate=ssl.CERT_REQUIRED)
            return_values['server'] = Server(host_name, port=port_number, use_ssl=True, tls=tls_object, get_info=ALL)
        #print("\nTrying to connect...")
        #print(server)
        return_values['conn'] = Connection(return_values['server'], version=3, user=user_name, password=password)
        #print("connection started")
        #conn.open() #bind implies open
        if not return_values['conn'].bind():
            return 0, "bind failed", return_values['conn'].results
        if want_tls == 'y':
            #print("starting tls\n")
            #conn.open()
            return_values['conn'].start_tls()
        #print(conn)
        return_values['exit_status'] = 1
        return_values['message'] = "Successfully connected!"
    except ldap3.LDAPSocketOpenError as err:
        if port_number != 636 and want_tls == 'y':
            return_values['message'] = "Invalid socket: Connecting with TLS may require a different port number."
        else:
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
        return_values['error'] = sys.exc_info()
    return return_values


def create_filter(attributes, num_attributes):
    """
    Returns a filter based on the number of attributes we want filtered.
    todo: add more number of attributes (currently only handles 3)
    """
    if num_attributes is 1:
        return '('+attributes[0]+'=*)'
    elif num_attributes is 2:
        return '(&(objectclass='+attributes[0]+')('+attributes[1]+'=*))'
    elif num_attributes is 3:
        return '(&(&('+attributes[0]+'='+attributes[1]+'))(objectclass='+attributes[2]+')('+attributes[3]+'=*))'


def ping_LDAP_server(host_name):
    """
    Checks if the given hostName is valid, and pings it.
    """
    try:
        host_name = socket.gethostbyname(host_name)
    except socket.gaierror:
        pass

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
    """
    Attempts to connect to the provided hostName and port number, default port is 389 if none provided.
    """
    conn_info = setup_connection(host_name, port_number, "", "", 'n', "")
    #if conn_info['exit_status'] == 1:
        #conn_info['conn'].unbind() front end will unbind for now
    return conn_info


def connect_LDAP_server(host_name, port_number, user_name, password, want_tls, tls_cert_path):
    """
    Attempts to connect to the provided hostName and port number, default port is 389 if none provided, using the provided user name and pass.
    Note: tls not working
    """
    conn_info = setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path)
    #if conn_info['exit_status'] == 1:
        #conn_info['conn'].unbind() front end will unbind for now
    return conn_info


def retrieve_server_info(conn, server):
    """
    Retrieves the information related to the server passed in.
    """
    try:
        assert conn.closed is not True
        serverinfo = open("serverinfo.txt", "w+") #note: doesn't matter that we overwrite serverinfo.txt bc users personal files should never be in this directory
        serverschema = open("serverschema.txt", "w+")
        print >>serverinfo, server.info
        print >>serverschema, server.schema
        serverinfo.close()
        serverschema.close()

        if conn.search('', '(objectclass=*)', ldap3.SEARCH_SCOPE_BASE_OBJECT, attributes=ldap3.ALL_ATTRIBUTES, get_operational_attributes=True) is True:
            version = ""
            server_type = ""
            i = 0
            try:
                version_result = conn.response[0]['attributes']['supportedLDAPVersion']
                for i in range(len(version_result) - 1):
                    version = version + str(version_result[i]) + ", "
                if len(version_result) == 1:
                    version = version + str(conn.response[0]['attributes']['supportedLDAPVersion'][i])
                else:
                    version = version + str(conn.response[0]['attributes']['supportedLDAPVersion'][i+1])
            except:
                version = "N/A"
            try:
                server_type = conn.response[0]['attributes']['structuralObjectClass']
            except:
                if str(server.info).lower().find("microsoft") != -1 and str(server.info).lower().find("active directory") != -1: 
                    server_type = "Active Directory"
                else:
                    server_type = "No server type found. (This usually means the server type is AD)"
            return {'exit_status': 1, 'version': "Supported LDAP Version: " + version, 'type': "LDAP Server Type: " + server_type}
    except:
        pass
    return {'exit_status': 0, 'version': None, 'type': None, 'error': sys.exc_info()}
    #dict = {'info': server.info, 'schema': server.schema}
    #return dict


def get_LDAP_suffix(server):
    """
    Returns the base dn of the ldap server
    """
    try:
        base_dn = str(server.info.naming_contexts[0])
        return {'exit_status': 1, 'base_dn': base_dn}
    except:
        return {'exit_status': 0, 'error': sys.exc_info}


def check_LDAP_suffix(conn, base_dn):
    """
    Checks that the given base_dn is the correct suffix for the given connection.
    """
    try:
        assert conn.closed is not True
        search_filter = create_filter(['cn'], 1)
        if conn.search(search_base=base_dn, search_filter=search_filter) is True:
            return {'exit_status': 1, 'message': "The given base DN is correct"}
    except:
        pass
    return {'exit_status': 0, 'message': "The given base DN is not correct"}


def list_user_related_OC(conn, user_dn, user_id_attribute):
    """
    Returns a list of the object classes related to the given user.
    """
    try:
        assert conn.closed is not True
        search_filter = create_filter([user_id_attribute], 1)
        if conn.search(search_base=user_dn, search_filter=search_filter, attributes=['objectclass']) is True:
            return {'exit_status': 1, 'objectclasses': conn.entries[0].objectclass.raw_values}
    except:
        pass
    return {'exit_status': 0, 'objectclasses': None}


def list_users(conn, user_dn, user_id_attribute, objectclass, limit):
    """
    Lists the users, up to the limit.
    """
    try:
        assert conn.closed is not True
        if limit is None:
            limit = 3
        search_filter = create_filter([objectclass, user_id_attribute], 2)
        if conn.search(search_base=user_dn, search_filter=search_filter, attributes=[user_id_attribute], size_limit=limit) is True:
            return {'exit_status': 1, 'users': conn.entries}
    except:
        pass
    return {'exit_status': 0, 'users': None}


def get_user(conn, user_dn, user_id_attribute, objectclass, user_name_attribute, name):
    """
    Returns a specific user.
    """
    try:
        assert conn.closed is not True
        search_filter = create_filter([user_name_attribute, name, objectclass, user_id_attribute], 3)
        if conn.search(search_base=user_dn, search_filter=search_filter, attributes=[user_id_attribute, user_name_attribute]) is True:
            return {'exit_status': 1, 'user': conn.entries}
    except:
        pass
    return {'exit_status': 0, 'user': None}


def list_group_related_OC(conn, group_dn, group_id_attribute):
    """
    Returns a list of object classes related to the given group.
    """
    try:
        assert conn.closed is not True
        search_filter = create_filter([group_id_attribute], 1)
        if conn.search(search_base=group_dn, search_filter=search_filter, attributes=['objectclass']) is True:
            return {'exit_status': 1, 'objectclasses': conn.entries[0].objectclass.raw_values}
    except:
        pass
    return {'exit_status': 0, 'objectclasses': None}


def list_groups(conn, group_dn, group_id_attribute, objectclass, limit):
    """
    Returns a list of groups, up to a limit.
    """
    try:
        assert conn.closed is not True
        if limit is None:
            limit = 3
        search_filter = create_filter([objectclass, group_id_attribute], 2)
        if conn.search(search_base=group_dn, search_filter=search_filter, attributes=[group_id_attribute], size_limit=limit) is True:
            return {'exit_status': 1, 'groups': conn.entries}
    except:
        pass
    return {'exit_status': 0, 'groups': None}


def get_group(conn, group_dn, group_id_attribute, objectclass, group_name_attribute, name):
    """
    Returns a specific group.
    """
    try:
        assert conn.closed is not True
        search_filter = create_filter([group_name_attribute, name, objectclass, group_id_attribute], 3)
        if conn.search(search_base=group_dn, search_filter=search_filter, attributes=[group_id_attribute, group_name_attribute]) is True:
            return {'exit_status': 1, 'group': conn.entries}
    except:
        pass
    return {'exit_status': 0, 'group': None}


def save_config(data, path):
    """
    Saves the passed in dictionary data to the specified file
    """
    try:
        fil = open(path, 'w')
    except:
        return {'exit_status': 0, 'message': "Unable to open file specified"}
    yaml.dump({'ldap': data}, fil, default_flow_style=False)
    return {'exit_status': 1, 'message': "Data successfully dumped"}
