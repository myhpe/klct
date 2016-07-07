import os
import ssl
import subprocess
import socket
import sys
import ldap3
from ldap3 import Server, Connection, ALL
import exceptions
import yaml

# if __name__ == "configTool" and __package__ is None:
#     parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     os.sys.path.append(parent_dir)
import log.log as log


def check_valid_IP(host_name):
    """
    Checks if the given hostName is a valid IP address.
    Return 1 if valid, 0 if invalid.
    """
    try:
        socket.inet_aton(host_name)
        log.success("Valid IP/Host Name entered")
        return 1
    except socket.error:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host_name)
        log.success("Valid IPv6 address entered")
        return 1
    except socket.error:
        log.failure("Invalid IP/Host Name entered")
        return 0


def setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path):
    """
    Sets up a connection given the parameters.
    Note: unbind the returned connection when finished using socket
    Note: need to find a way to check validation of certificate, eg. expiration, etc
    """
    return_values = {'exit_status': 0, 'message': None, 'error': None, 'server': None, 'conn': None}
    if port_number is None and want_tls == 'n':
        log.success("tls conection not required, setting default port to 389")
        port_number = 389
    elif port_number is None and want_tls == 'y':
        log.success("tls conection not required, setting default port to 636")
        port_number = 636
    try:
        log.success("Attempting to create server object with port: " + str(port_number) + ", username: " + str(user_name) + ", password: " + str(password) + ", tls_requested: " + want_tls + ", certificate path: " + str(tls_cert_path))
        if want_tls == 'n':
            return_values['server'] = Server(host_name, port=port_number, get_info=ALL)
        else:
            log.success("Attempting to create tls object with certificate file " + tls_cert_path)
            try:
                subprocess.check_output(["openssl", "x509", "-checkend", "120", "-noout", "-in", tls_cert_path], stderr=subprocess.STDOUT, universal_newlines=True)
                log.success("Tls certificate is valid")
            except:
                log.failure("Tls certificate has expired or will expire within the next 2 minutes")
                return_values['message'] = "Tls certificate has expired or will expire within the next 2 minutes"
                return return_values

            tls_object = ldap3.Tls(ca_certs_file=tls_cert_path, validate=ssl.CERT_REQUIRED)
            return_values['server'] = Server(host_name, port=port_number, use_ssl=True, tls=tls_object, get_info=ALL)
            log.success("Successfully created tls object")
        log.success("Successfully created server object")
        log.success("Attempting to create connection socket")
        return_values['conn'] = Connection(return_values['server'], user=user_name, password=password)
        log.success("Successfully created socket")
        log.success("Attempting to bind to socket")
        if not return_values['conn'].bind():
            log.failure("Failed to bind to socket")
            return_values['message'] = "Failed to bind to socket (Invalid Log in credentials)"
            return return_values
        log.success("Successfully bound to socket")
        if want_tls == 'y':
            log.success("Attempting to start tls on connection")
            return_values['conn'].start_tls()
            log.success("Successfully started tls")
        return_values['exit_status'] = 1
        return_values['message'] = "Successfully connected!"
        log.success(str(return_values['message']))
        #log.success("results: " + return_values['conn'].results)
        return return_values
    except ldap3.LDAPSocketOpenError as err:
        if port_number != 636 and want_tls == 'y':
            return_values['message'] = "Invalid socket: Connecting with TLS may require a different port number."
        else:
            return_values['message'] = "Failed to connect due to invalid socket."
        return_values['error'] = err
    except ldap3.LDAPInvalidPortError as err:
        return_values['message'] = "Invalid Port"
        return_values['error'] = err
    except ldap3.LDAPPasswordIsMandatoryError as err:
        return_values['message'] = "Please enter a password"
        return_values['error'] = err
    except ldap3.core.exceptions.LDAPStartTLSError as err:
        return_values['message'] = "Unable to start TLS"
        return_values['error'] = err
    except:
        return_values['message'] = "Failed to connect due to unknown reasons"
        return_values['error'] = sys.exc_info()
    if return_values['error'] is not None:
        log.failure("Error: " + str(return_values['error']))
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
    log.success("Initializing ping sequence to \"" + host_name + "\"")
    try:
        old_host = host_name
        host_name = socket.gethostbyname(host_name)
        log.success("Converted \"" + old_host + "\" to an ip: \"" + host_name + "\"")
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
            log.success("Successfully pinged \"" + host_name + "\"")
        except subprocess.CalledProcessError:
            response = 0
            log.failure("Unsuccessfully pinged \"" + host_name + "\"")
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
    log.success("Initializing connection to \"" + host_name + "\"")
    conn_info = setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path)
    #if conn_info['exit_status'] == 1:
        #conn_info['conn'].unbind() front end will unbind for now
    return conn_info


def retrieve_server_info(conn, server):
    """
    Retrieves the information related to the server passed in.
    """
    return_values = {'exit_status': 0, 'version': None, 'type': None, 'error': None}
    try:
        log.success("Attempting to retrieve server Info")
        assert conn.closed is not True
        log.success("Connection socket is open")
        log.success("Creating serverinfo and serverschema files")
        serverinfo = open("serverinfo.txt", "w+") #note: doesn't matter that we overwrite serverinfo.txt bc users personal files should never be in this directory
        serverschema = open("serverschema.txt", "w+")
        log.success("Dumping serverinfo and serverschema to the respective files")
        print >>serverinfo, server.info
        print >>serverschema, server.schema
        log.success("Closing serverinfo and serverschema files")
        serverinfo.close()
        serverschema.close()

        log.success("Searching for ldap attributes")
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
                log.success("Found supported ldap versions: " + version)
            except:
                log.failure("Unable to find supported ldap versions")
                version = "N/A"
            try:
                server_type = conn.response[0]['attributes']['structuralObjectClass']
                log.success("Found ldap server type: " + server_type)
            except:
                if str(server.info).lower().find("microsoft") != -1 and str(server.info).lower().find("active directory") != -1:
                    log.success("Found ldap server type: Active Directory")
                    server_type = "Active Directory"
                else:
                    log.failure("Unable to find ldap server type")
                    server_type = "No server type found. (This usually means the server type is AD)"
            return_values['exit_status'] = 1
            return_values['version'] = "Supported LDAP Version: " + version
            return_values['type'] = "LDAP Server Type: " + server_type
            return return_values
    except exceptions.AssertionError as err:
        return_vaules['error'] = err
    except:
        return_values['error'] = sys.exc_info()
    log.failure(return_values['error'])
    return return_values
    #dict = {'info': server.info, 'schema': server.schema}
    #return dict


def get_LDAP_suffix(server):
    """
    Returns the base dn of the ldap server
    """
    log.success("Discovering suffix (base DN) from server information")
    try:
        base_dn = str(server.info.naming_contexts[0])
        log.success("Found suffix (base DN): " + base_dn)
        return {'exit_status': 1, 'base_dn': base_dn}
    except:
        log.failure("Unable to find suffix (base DN)")
        return {'exit_status': 0, 'error': sys.exc_info}


def check_LDAP_suffix(conn, base_dn):
    """
    Checks that the given base_dn is the correct suffix for the given connection.
    """
    log.success("Validating given base suffix (base DN): " + base_dn)
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        search_filter = create_filter(['cn'], 1)
        log.success("Created search filter: " + search_filter)
        if conn.search(search_base=base_dn, search_filter=search_filter) is True:
            log.success("Suffix (base DN) is verified")
            return {'exit_status': 1, 'message': "The given base DN is correct"}
        else:
            log.failure(base_dn + " is an invalid suffix (base DN)")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'message': "Connection is closed", 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'message': "The given base DN is not correct", 'error': sys.exc_info()}

def validate_suffix(conn, dn, id_attribute, name_attribute):
    """
    Checks that the given dn is valid.
    """
    log.success("Validating given DN: " + dn)
    try:
        assert conn.closed is not True
        log.success("connection is open")
        search_filter = create_filter()
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'message': "Connection is closed", 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'message': "", 'error': sys.exc_info()}


def list_user_related_OC(conn, user_dn, user_id_attribute):
    """
    Returns a list of the object classes related to the given user.
    """
    log.success("Searching for user related object classes")
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        search_filter = create_filter([user_id_attribute], 1)
        log.success("Created search filter: " + search_filter)
        if conn.search(search_base=user_dn, search_filter=search_filter, attributes=['objectclass']) is True:
            log.success("Found object classes: " + str(conn.entries[0].objectclass.raw_values))
            return {'exit_status': 1, 'objectclasses': conn.entries[0].objectclass.raw_values}
        else:
            log.failure("No user related object classes found")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'objectclasses': None, 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'objectclasses': None, 'error': sys.exc_info()}


def list_users(conn, user_dn, user_id_attribute, objectclass, limit):
    """
    Lists the users, up to the limit.
    """
    log.success("Searching for a list of users")
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        if limit is None:
            log.success("No limit entered, using 3 as default")
            limit = 3
        search_filter = create_filter([objectclass, user_id_attribute], 2)
        log.success("created seach filter: " + search_filter)
        if conn.search(search_base=user_dn, search_filter=search_filter, attributes=[user_id_attribute], size_limit=limit) is True:
            log.success("Found list of users: " + str(conn.entries))
            return {'exit_status': 1, 'users': conn.entries}
        else:
            log.failure("No users found")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'users': None, 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'users': None, 'error': sys.exc_info()}


def get_user(conn, user_dn, user_id_attribute, objectclass, user_name_attribute, name):
    """
    Returns a specific user.
    """
    log.success("Searching for user: " + name)
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        search_filter = create_filter([user_name_attribute, name, objectclass, user_id_attribute], 3)
        log.success("created seach filter: " + search_filter)
        if conn.search(search_base=user_dn, search_filter=search_filter, attributes=[user_id_attribute, user_name_attribute]) is True:
            log.success("Found user: " + str(conn.entries))
            return {'exit_status': 1, 'user': conn.entries}
        else:
            log.failure("User " + name + " not found")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'user': None, 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'user': None, 'error': sys.exc_info()}


def list_group_related_OC(conn, group_dn, group_id_attribute):
    """
    Returns a list of object classes related to the given group.
    """
    log.success("Searching for group related object classes")
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        search_filter = create_filter([group_id_attribute], 1)
        log.success("created seach filter: " + search_filter)
        if conn.search(search_base=group_dn, search_filter=search_filter, attributes=['objectclass']) is True:
            log.success("Found object classes: " + str(conn.entries[0].objectclass.raw_values))
            return {'exit_status': 1, 'objectclasses': conn.entries[0].objectclass.raw_values}
        else:
            log.failure("No group related object classes found")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'objectclasses': None, 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'objectclasses': None, 'error': sys.exc_info()}


def list_groups(conn, group_dn, group_id_attribute, objectclass, limit):
    """
    Returns a list of groups, up to a limit.
    """
    log.success("Searching for a list of groups")
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        if limit is None:
            log.success("No limit entered, using 3 as default")
            limit = 3
        search_filter = create_filter([objectclass, group_id_attribute], 2)
        log.success("created seach filter: " + search_filter)
        if conn.search(search_base=group_dn, search_filter=search_filter, attributes=[group_id_attribute], size_limit=limit) is True:
            log.success("Found list of groups: " + str(conn.entries))
            return {'exit_status': 1, 'groups': conn.entries}
        else:
            log.failure("No groups found")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'groups': None, 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'groups': None, 'error': sys.exc_info()}


def get_group(conn, group_dn, group_id_attribute, objectclass, group_name_attribute, name):
    """
    Returns a specific group.
    """
    log.success("Searching for group: " + name)
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        search_filter = create_filter([group_name_attribute, name, objectclass, group_id_attribute], 3)
        log.success("created seach filter: " + search_filter)
        if conn.search(search_base=group_dn, search_filter=search_filter, attributes=[group_id_attribute, group_name_attribute]) is True:
            log.success("Found group: " + str(conn.entries))
            return {'exit_status': 1, 'group': conn.entries}
        else:
            log.failure("Group " + name + " not found")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'group': None, 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'group': None, 'error': err}


def save_config(data, path):
    """
    Saves the passed in dictionary data to the specified file
    """
    try:
        log.success("Attempting to open file: " + path)
        fil = open(path, 'w')
    except:
        log.failure("Unable to open file: " + path)
        log.failure(sys.exc_info())
        return {'exit_status': 0, 'message': "Unable to open file specified"}
    log.success("Dumping configuration options: " + str(data) + " to file: " + path)
    yaml.dump({'ldap': data}, fil, default_flow_style=False)
    return {'exit_status': 1, 'message': "Data successfully dumped"}
