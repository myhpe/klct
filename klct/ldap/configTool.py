import os
import ssl
import subprocess
import socket
import sys
import ldap3
from ldap3 import Server, Connection, ALL
import exceptions
import yaml
import copy

# if __name__ == "configTool" and __package__ is None:
#     parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     os.sys.path.append(parent_dir)
import log.log as log


def _check_valid_IP(host_name):
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


def _setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path):
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


def _create_filter(attributes, num_attributes):
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


def ping_ldap_server(host_name):
    """
    Checks if the given hostName is valid, and pings it.
    """
    log.success("Initializing ping sequence to " + host_name)
    return_values = {'exit_status': 0, 'host_name': host_name, 'message': None}
    try:
        new_host_name = socket.gethostbyname(host_name)
        log.success("Converted " + host_name + " to an ip: " + new_host_name)
    except socket.gaierror:
        log.failure("Unable to convert " + host_name)
        pass

<<<<<<< HEAD
    is_valid = check_valid_IP(new_host_name)
=======
    is_valid = _check_valid_IP(new_host_name)
>>>>>>> d8737c438399e06276cbfa3a5f8e525c45401e67
    if not is_valid or host_name == "":
        return_values['message'] = host_name + " is an invalid host name"
        return return_values

    with open(os.devnull, "w"):
        try:
            subprocess.check_output(["ping", "-c", "1", host_name], stderr=subprocess.STDOUT, universal_newlines=True)
            log.success("Successfully pinged " + host_name)
            return_values['exit_status'] = 1
            return_values['message'] = "Successfully pinged " + host_name
        except subprocess.CalledProcessError:
            log.failure("Unsuccessfully pinged " + host_name)
            return_values['exit_status'] = 0
            return_values['message'] = "Unsuccessfully pinged " + host_name

    if host_name == new_host_name:
        return_values['host_name'] = "ldap://" + host_name
    else:
        return_values['host_name'] = host_name
    return return_values


def connect_LDAP_server_basic(host_name, port_number):
    """
    Attempts to connect to the provided hostName and port number, default port is 389 if none provided.
    """
    conn_info = _setup_connection(host_name, port_number, "", "", 'n', "")
    #if conn_info['exit_status'] == 1:
        #conn_info['conn'].unbind() front end will unbind for now
    return conn_info


def connect_LDAP_server(host_name, port_number, user_name, password, want_tls, tls_cert_path):
    """
    Attempts to connect to the provided hostName and port number, default port is 389 if none provided, using the provided user name and pass.
    Note: tls not working
    """
    log.success("Initializing connection to \"" + host_name + "\"")
    conn_info = _setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path)
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

        orig_stdout = sys.stdout

        sys.stdout = open("serverinfo.txt", "w+") #note: doesn't matter that we overwrite serverinfo.txt bc users personal files should never be in this directory
        print(server.info)
        sys.stdout.close()

        sys.stdout = open("serverschema.txt", "w+")
        print(server.schema)
        sys.stdout.close()

        sys.stdout = orig_stdout

        log.success("Dumping serverinfo and serverschema to the respective files")
        # print >>serverinfo, server.info
        # print >>serverschema, server.schema
        log.success("Closing serverinfo and serverschema files")

        log.success("Searching for ldap attributes")
        if conn.search('', '(objectclass=*)', ldap3.SEARCH_SCOPE_BASE_OBJECT, attributes=ldap3.ALL_ATTRIBUTES, get_operational_attributes=True) is True and conn.entries:
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
        return_values['error'] = err
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
        search_filter = _create_filter(['cn'], 1)
        log.success("Created search filter: " + search_filter)
        if conn.search(search_base=base_dn, search_filter=search_filter) is True and conn.entries:
            log.success(base_dn + " is a valid suffix (base DN)")
            return {'exit_status': 1, 'message': base_dn + " is a valid suffix (base DN)"}
        else:
            log.failure(base_dn + " is an invalid suffix (base DN)")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'message': "Connection is closed", 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'message': base_dn + " is an invalid suffix (base DN)", 'error': sys.exc_info()}


def validate_info(conn, dn, id_attribute, name_attribute):
    """
    Checks that the given dn is valid. If so, it will validate the id_attribute and name_attribute as well.
    """
    log.success("Validating given DN: " + dn)
    return_values = {'exit_status': 1, 'message': None, 'error': None}
    try:
        assert conn.closed is not True
        log.success("Connection is open")

        if conn.search(search_base=dn, search_scope=ldap3.LEVEL, search_filter='(objectclass=*)', attributes=[ldap3.ALL_ATTRIBUTES], size_limit=1) is True and conn.entries:
            log.success(dn + " is a valid DN")
            if id_attribute in conn.entries[0]:
                log.success(id_attribute + " is a valid id attribute")
            else:
                log.failure(id_attribute + " is an invalid id attribute")
                return_values['exit_status'] = 0
                return_values['message'] = id_attribute + " is an invalid id attribute"
            if name_attribute in conn.entries[0]:
                log.success(name_attribute + " is a valid name attribute")
            else:
                log.failure(name_attribute + " is an invalid name attribute")
                return_values['exit_status'] = 0
                if return_values['message'] == None:
                    return_values['message'] = name_attribute + " is an invalid name attribute"
                else:
                    return_values['message'] = name_attribute + " is a valid name attribute"
            if return_values['exit_status'] == 1:
                return_values['message'] = dn + ", " + id_attribute + ", and " + name_attribute + " are valid"
            return return_values
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'message': "Connection is closed", 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'message': dn + " is an invalid DN", 'error': sys.exc_info()}


def list_object_classes(conn, dn, id_attribute):
    """
    Returns a list of the object classes.
    """
    log.success("Searching for object classes")
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        search_filter = _create_filter([id_attribute], 1)
        log.success("Created search filter: " + search_filter)
        if conn.search(search_base=dn, search_scope=ldap3.LEVEL, search_filter=search_filter, attributes=['objectclass']) is True and conn.entries:
            objclasses_list = []
            for objclass_list in conn.entries:
                for objclass in objclass_list.objectclass:
                    if objclass not in objclasses_list:
                        objclasses_list.append(objclass)
            log.success("Found object classes: " + str(objclasses_list))
            return {'exit_status': 1, 'objectclasses': objclasses_list}
        else:
            log.failure("No object classes found")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'objectclasses': None, 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'objectclasses': None, 'error': sys.exc_info()}


def validate_object_class(conn, dn, objectclass):
    log.success("Searching for object classes")
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        search_filter = '(objectclass='+objectclass+')'
        log.success("Created search filter: " + search_filter)
        if conn.search(search_base=dn, search_filter=search_filter, size_limit=1) is True and conn.entries:
            log.success(objectclass + " is a valid objectclass")
            return {'exit_status': 1, 'message': objectclass + " is a valid objectclass", 'error': None}
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'message': "Connection is closed", 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'message': objectclass + " is an invalid objectclass", 'error': sys.exc_info()}


def list_entries(conn, dn, id_attribute, objectclass, limit):
    """
    Lists the entries, up to the limit.
    """
    log.success("Searching for a list of users")
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        if limit is None:
            log.success("No limit entered, using 3 as default")
            limit = 3
        search_filter = _create_filter([objectclass, id_attribute], 2)
        log.success("Created search filter: " + search_filter)
        if conn.search(search_base=dn, search_scope=ldap3.LEVEL, search_filter=search_filter, size_limit=limit) is True and conn.entries:
            log.success("Found list of entries: " + str(conn.entries))
            return {'exit_status': 1, 'entries': conn.entries}
        else:
            log.failure("No entries found")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'entries': None, 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'entries': None, 'error': sys.exc_info()}


def get_entry(conn, dn, id_attribute, objectclass, name_attribute, name):
    """
    Returns a specific user.
    """
    log.success("Searching for entry: " + name)
    try:
        assert conn.closed is not True
        log.success("Connection is open")
        search_filter = _create_filter([name_attribute, name, objectclass, id_attribute], 3)
        log.success("Created search filter: " + search_filter)
        if conn.search(search_base=dn, search_filter=search_filter) is True and conn.entries:
            if len(conn.entries) > 1:
                log.failure("Duplicate entries found for: " + name)
                return{'exit_status': 0, 'entry': conn.entries, 'error': "Duplicate entries found"}
            log.success("Found entry: " + str(conn.entries))
            return {'exit_status': 1, 'entry': conn.entries}
        else:
            log.failure("Entry: " + name + " not found")
    except exceptions.AssertionError as err:
        log.failure(err)
        return {'exit_status': 0, 'entry': None, 'error': err}
    except:
        log.failure(sys.exc_info())
    return {'exit_status': 0, 'entry': None, 'error': sys.exc_info()}


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
    fil.close()
    return {'exit_status': 1, 'message': "Data successfully dumped"}

