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
# import klct.log.log as log
import logging

LOG = logging.getLogger("log")


def _check_valid_IP(host_name):
    """
    Checks if the given hostName is a valid IP address.
    Return 1 if valid, 0 if invalid.
    """
    try:
        socket.inet_aton(host_name)
        LOG.info("Valid IP/Host Name entered")
        return 1
    except socket.error:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host_name)
        LOG.info("Valid IPv6 address entered")
        return 1
    except socket.error:
        LOG.warning("Invalid IP/Host Name entered")
        return 0


def _setup_connection(host_name, port_number, user_name, password, want_tls,
                      tls_cert_path):
    """
    Sets up a connection given the parameters.
    Note: unbind the returned connection when finished using socket
    Note: need to find a way to check validation of certificate,
    eg. expiration, etc
    """
    ret_vals = {'exit_status': 0, 'message': None, 'error': None,
                'server': None, 'conn': None}
    if port_number is None and want_tls == 'n':
        LOG.info("tls conection not required, setting default port to 389")
        port_number = 389
    elif port_number is None and want_tls == 'y':
        LOG.info("tls conection not required, setting default port to 636")
        port_number = 636
    try:
        LOG.info("Attempting to create server object with port: " + str(
            port_number) + ", username: " + str(
            user_name) + ", password: " + str(
            password) + ", tls_requested: " + want_tls +
                 ", certificate path: " + str(tls_cert_path))
        if want_tls == 'n':
            ret_vals['server'] = Server(host_name, port=port_number,
                                        get_info=ALL)
        else:
            LOG.info("Attempting to create tls object with certificate file "
                     "" + tls_cert_path)
            try:
                subprocess.check_output(["openssl", "x509", "-checkend",
                                         "120", "-noout", "-in",
                                         tls_cert_path],
                                        stderr=subprocess.STDOUT,
                                        universal_newlines=True)
                LOG.info("Tls certificate is valid")
            except:
                LOG.warning("Tls certificate has expired or will expire "
                            "within the next 2 minutes")
                ret_vals['message'] = "Tls certificate has expired or will " \
                                      "expire within the next 2 minutes"
                return ret_vals

            tls_object = ldap3.Tls(ca_certs_file=tls_cert_path,
                                   validate=ssl.CERT_REQUIRED)
            ret_vals['server'] = Server(host_name, port=port_number,
                                        use_ssl=True, tls=tls_object,
                                        get_info=ALL)
            LOG.info("Successfully created tls object")
        LOG.info("Successfully created server object")
        LOG.info("Attempting to create connection socket")
        ret_vals['conn'] = Connection(ret_vals['server'], user=user_name,
                                      password=password)
        LOG.info("Successfully created socket")
        LOG.info("Attempting to bind to socket")
        if not ret_vals['conn'].bind():
            LOG.warning("Failed to bind to socket")
            ret_vals['message'] = "Failed to bind to socket (Invalid Log in " \
                                  "credentials)"
            return ret_vals
        LOG.info("Successfully bound to socket")
        if want_tls == 'y':
            LOG.info("Attempting to start tls on connection")
            ret_vals['conn'].start_tls()
            LOG.info("Successfully started tls")
        ret_vals['exit_status'] = 1
        ret_vals['message'] = "Successfully connected!"
        LOG.info(str(ret_vals['message']))
        return ret_vals
    except ldap3.LDAPSocketOpenError as err:
        if port_number != 636 and want_tls == 'y':
            ret_vals['message'] = "Invalid socket: Connecting with TLS " \
                                       "may require a different port number."
        else:
            ret_vals['message'] = "Failed to connect due to invalid " \
                                       "socket."
        ret_vals['error'] = err
    except ldap3.LDAPInvalidPortError as err:
        ret_vals['message'] = "Invalid Port"
        ret_vals['error'] = err
    except ldap3.LDAPPasswordIsMandatoryError as err:
        ret_vals['message'] = "Please enter a password"
        ret_vals['error'] = err
    except ldap3.core.exceptions.LDAPStartTLSError as err:
        ret_vals['message'] = "Unable to start TLS"
        ret_vals['error'] = err
    except:
        ret_vals['message'] = "Failed to connect due to unknown reasons"
        ret_vals['error'] = sys.exc_info()
    if ret_vals['error'] is not None:
        LOG.warning("Error: " + str(ret_vals['error']))
    return ret_vals


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
        return '(&(&(' + attributes[0] + '=' + attributes[1] + '))(' \
                                                        'objectclass=' \
               + attributes[2] + ')(' + attributes[3] + '=*))'


def ping_ldap_server(host_name):
    """
    Checks if the given hostName is valid, and pings it.
    """
    LOG.info("Initializing ping sequence to " + host_name)
    ret_vals = {'exit_status': 0, 'host_name': host_name, 'message': None}
    new_host_name = ""
    try:
        new_host_name = socket.gethostbyname(host_name)
        LOG.info("Converted " + host_name + " to an ip: " + new_host_name)
    except socket.gaierror:
        LOG.warning("Unable to convert " + host_name)
        pass

    is_valid = _check_valid_IP(new_host_name)
    if not is_valid or host_name == "":
        ret_vals['message'] = host_name + " is an invalid host name"
        return ret_vals

    with open(os.devnull, "w"):
        try:
            subprocess.check_output(["ping", "-c", "1", host_name],
                                    stderr=subprocess.STDOUT,
                                    universal_newlines=True)
            LOG.info("Successfully pinged " + host_name)
            ret_vals['exit_status'] = 1
            ret_vals['message'] = "Successfully pinged " + host_name
        except subprocess.CalledProcessError:
            LOG.warning("Unsuccessfully pinged " + host_name)
            ret_vals['exit_status'] = 0
            ret_vals['message'] = "Unsuccessfully pinged " + host_name

    if host_name == new_host_name:
        ret_vals['host_name'] = "ldap://" + host_name
    else:
        ret_vals['host_name'] = host_name
    return ret_vals


def connect_ldap_server_basic(host_name, port_number):
    """
    Attempts to connect to the provided hostName and port number, default
    port is 389 if none provided.
    """
    conn_info = _setup_connection(host_name, port_number, "", "", 'n', "")
    # if conn_info['exit_status'] == 1:
    #     conn_info['conn'].unbind() front end will unbind for now
    return conn_info


def connect_ldap_server(host_name, port_number, user_name, password,
                        want_tls, tls_cert_path):
    """
    Attempts to connect to the provided hostName and port number, default
    port is 389 if none provided, using the provided user name and pass.
    Note: tls not working
    """
    LOG.info("Initializing connection to \"" + host_name + "\"")
    conn_info = _setup_connection(host_name, port_number, user_name, password,
                                  want_tls, tls_cert_path)
    # if conn_info['exit_status'] == 1:
    #     conn_info['conn'].unbind() front end will unbind for now
    return conn_info


def retrieve_server_info(conn, server):
    """
    Retrieves the information related to the server passed in.
    """
    ret_vals = {'exit_status': 0, 'version': None, 'type': None, 'error': None}
    try:
        LOG.info("Attempting to retrieve server Info")
        assert conn.closed is not True
        LOG.info("Connection socket is open")
        LOG.info("Creating serverinfo and serverschema files")

        orig_stdout = sys.stdout

        sys.stdout = open("serverinfo.txt", "w+")  # note: doesn't matter
        # that we overwrite serverinfo.txt bc users personal files should
        # never be in this directory
        print(server.info)
        sys.stdout.close()

        sys.stdout = open("serverschema.txt", "w+")
        print(server.schema)
        sys.stdout.close()

        sys.stdout = orig_stdout

        LOG.info("Dumping serverinfo and serverschema to the respective files")
        # print >>serverinfo, server.info
        # print >>serverschema, server.schema
        LOG.info("Closing serverinfo and serverschema files")

        LOG.info("Searching for ldap attributes")
        if conn.search('', '(objectclass=*)', ldap3.SEARCH_SCOPE_BASE_OBJECT,
                       attributes=ldap3.ALL_ATTRIBUTES,
                       get_operational_attributes=True) is True \
                and conn.entries:
            version = ""
            server_type = ""
            i = 0
            try:
                version_result = \
                    conn.response[0]['attributes']['supportedLDAPVersion']
                for i in range(len(version_result) - 1):
                    version = version + str(version_result[i]) + ", "
                if len(version_result) == 1:
                    version = version + str(version_result[i])
                else:
                    version = version + str(version_result[i+1])
                LOG.info("Found supported ldap versions: " + version)
            except:
                LOG.warning("Unable to find supported ldap versions")
                version = "N/A"
            try:
                server_type = conn.response[0]['attributes'][
                    'structuralObjectClass']
                LOG.info("Found ldap server type: " + server_type)
            except:
                if str(server.info).lower().find("microsoft") != -1 and str(
                        server.info).lower().find("active directory") != -1:
                    LOG.info("Found ldap server type: Active Directory")
                    server_type = "Active Directory"
                else:
                    LOG.warning("Unable to find ldap server type")
                    server_type = "No server type found. (This usually " \
                                  "means the server type is AD)"
            ret_vals['exit_status'] = 1
            ret_vals['version'] = "Supported LDAP Version: " + version
            ret_vals['type'] = "LDAP Server Type: " + server_type
            return ret_vals
    except exceptions.AssertionError as err:
        ret_vals['error'] = err
    except:
        ret_vals['error'] = sys.exc_info()
    LOG.warning(ret_vals['error'])
    return ret_vals
    # dict = {'info': server.info, 'schema': server.schema}
    # return dict


def get_ldap_suffix(server):
    """
    Returns the base dn of the ldap server
    """
    LOG.info("Discovering suffix (base DN) from server information")
    try:
        base_dn = str(server.info.naming_contexts[0])
        LOG.info("Found suffix (base DN): " + base_dn)
        return {'exit_status': 1, 'base_dn': base_dn}
    except:
        LOG.warning("Unable to find suffix (base DN)")
        return {'exit_status': 0, 'error': sys.exc_info}


def check_ldap_suffix(conn, base_dn):
    """
    Checks that the given base_dn is the correct suffix for the given
    connection.
    """
    LOG.info("Validating given base suffix (base DN): " + base_dn)
    try:
        assert conn.closed is not True
        LOG.info("Connection is open")
        search_filter = _create_filter(['cn'], 1)
        LOG.info("Created search filter: " + search_filter)
        if conn.search(search_base=base_dn, search_filter=search_filter) is \
                True and conn.entries:
            LOG.info(base_dn + " is a valid suffix (base DN)")
            return {'exit_status': 1, 'message': base_dn + " is a valid "
                                                           "suffix (base DN)"}
        else:
            LOG.warning(base_dn + " is an invalid suffix (base DN)")
    except exceptions.AssertionError as err:
        LOG.warning(err)
        return {'exit_status': 0, 'message': "Connection is closed",
                'error': err}
    except:
        LOG.warning(sys.exc_info())
    return {'exit_status': 0,
            'message': base_dn + " is an invalid suffix (base DN)",
            'error': sys.exc_info()}


def validate_info(conn, dn, id_attribute, name_attribute):
    """
    Checks that the given dn is valid. If so, it will validate the
    id_attribute and name_attribute as well.
    """
    LOG.info("Validating given DN: " + dn)
    ret_vals = {'exit_status': 1, 'message': None, 'error': None}
    try:
        assert conn.closed is not True
        LOG.info("Connection is open")

        if conn.search(search_base=dn, search_scope=ldap3.LEVEL,
                       search_filter='(objectclass=*)',
                       attributes=[ldap3.ALL_ATTRIBUTES],
                       size_limit=1) is True and conn.entries:
            LOG.info(dn + " is a valid DN")
            if id_attribute in conn.entries[0]:
                LOG.info(id_attribute + " is a valid id attribute")
            else:
                LOG.warning(id_attribute + " is an invalid id attribute")
                ret_vals['exit_status'] = 0
                ret_vals['message'] = id_attribute + " is an invalid id " \
                                                     "attribute"
            if name_attribute in conn.entries[0]:
                LOG.info(name_attribute + " is a valid name attribute")
            else:
                LOG.warning(name_attribute + " is an invalid name attribute")
                ret_vals['exit_status'] = 0
                if ret_vals['message'] is None:
                    ret_vals['message'] = name_attribute + \
                                               " is an invalid name attribute"
                else:
                    ret_vals['message'] = name_attribute + \
                                               " is a valid name attribute"
            if ret_vals['exit_status'] == 1:
                ret_vals['message'] = dn + ", " \
                                           + id_attribute \
                                           + ", and " + name_attribute\
                                           + " are valid"
            return ret_vals
    except exceptions.AssertionError as err:
        LOG.warning(err)
        return {'exit_status': 0, 'message': "Connection is closed",
                'error': err}
    except:
        LOG.warning(sys.exc_info())
    return {'exit_status': 0, 'message': dn + " is an invalid DN",
            'error': sys.exc_info()}


def list_object_classes(conn, dn, id_attribute):
    """
    Returns a list of the object classes.
    """
    LOG.info("Searching for object classes")
    try:
        assert conn.closed is not True
        LOG.info("Connection is open")
        search_filter = _create_filter([id_attribute], 1)
        LOG.info("Created search filter: " + search_filter)
        if conn.search(search_base=dn, search_scope=ldap3.LEVEL,
                       search_filter=search_filter,
                       attributes=['objectclass']) is True and conn.entries:
            objclasses_list = []
            for objclass_list in conn.entries:
                for objclass in objclass_list.objectclass:
                    if objclass not in objclasses_list:
                        objclasses_list.append(objclass)
            LOG.info("Found object classes: " + str(objclasses_list))
            return {'exit_status': 1, 'objectclasses': objclasses_list}
        else:
            LOG.warning("No object classes found")
    except exceptions.AssertionError as err:
        LOG.warning(err)
        return {'exit_status': 0, 'objectclasses': None, 'error': err}
    except:
        LOG.warning(sys.exc_info())
    return {'exit_status': 0, 'objectclasses': None, 'error': sys.exc_info()}


def validate_object_class(conn, dn, objectclass):
    LOG.info("Searching for object classes")
    try:
        assert conn.closed is not True
        LOG.info("Connection is open")
        search_filter = '(objectclass='+objectclass+')'
        LOG.info("Created search filter: " + search_filter)
        if conn.search(search_base=dn, search_filter=search_filter,
                       size_limit=1) is True and conn.entries:
            LOG.info(objectclass + " is a valid objectclass")
            return {'exit_status': 1, 'message': objectclass + " is a valid "
                                                               "objectclass",
                    'error': None}
    except exceptions.AssertionError as err:
        LOG.warning(err)
        return {'exit_status': 0, 'message': "Connection is closed",
                'error': err}
    except:
        LOG.warning(sys.exc_info())
    return {'exit_status': 0, 'message': objectclass + " is an invalid "
                                                       "objectclass",
            'error': sys.exc_info()}


def list_entries(conn, dn, id_attribute, objectclass, limit):
    """
    Lists the entries, up to the limit.
    """
    LOG.info("Searching for a list of users")
    try:
        assert conn.closed is not True
        LOG.info("Connection is open")
        if limit is None:
            LOG.info("No limit entered, using 3 as default")
            limit = 3
        search_filter = _create_filter([objectclass, id_attribute], 2)
        LOG.info("Created search filter: " + search_filter)
        if conn.search(search_base=dn, search_scope=ldap3.LEVEL,
                       search_filter=search_filter,
                       attributes=[ldap3.ALL_ATTRIBUTES],
                       size_limit=limit) is True and conn.entries:
            LOG.info("Found list of entries: " + str(conn.entries))
            return {'exit_status': 1, 'entries': conn.entries}
        else:
            LOG.warning("No entries found")
    except exceptions.AssertionError as err:
        LOG.warning(err)
        return {'exit_status': 0, 'entries': None, 'error': err}
    except:
        LOG.warning(sys.exc_info())
    return {'exit_status': 0, 'entries': None, 'error': sys.exc_info()}


def get_entry(conn, dn, id_attribute, objectclass, name_attribute, name):
    """
    Returns a specific user.
    """
    LOG.info("Searching for entry: " + name)
    try:
        assert conn.closed is not True
        LOG.info("Connection is open")
        search_filter = _create_filter([name_attribute, name, objectclass,
                                        id_attribute], 3)
        LOG.info("Created search filter: " + search_filter)
        if conn.search(search_base=dn, search_filter=search_filter,
                       attributes=[ldap3.ALL_ATTRIBUTES]) is True and \
                conn.entries:
            if len(conn.entries) > 1:
                LOG.warning("Duplicate entries found for: " + name)
                return{'exit_status': 0, 'entry': conn.entries,
                       'error': "Duplicate entries found"}
            LOG.info("Found entry: " + str(conn.entries))
            return {'exit_status': 1, 'entry': conn.entries}
        else:
            LOG.warning("Entry: " + name + " not found")
    except exceptions.AssertionError as err:
        LOG.warning(err)
        return {'exit_status': 0, 'entry': None, 'error': err}
    except:
        LOG.warning(sys.exc_info())
    return {'exit_status': 0, 'entry': None, 'error': sys.exc_info()}


def save_config(data, path):
    """
    Saves the passed in dictionary data to the specified file
    """
    try:
        LOG.info("Attempting to open file: " + path)
        fil = open(path, 'w')
    except:
        LOG.warning("Unable to open file: " + path)
        LOG.warning(sys.exc_info())
        return {'exit_status': 0, 'message': "Unable to open file specified"}
    LOG.info("Dumping configuration options: " + str(data) + " to file: " +
             path)
    yaml.dump({'ldap': data}, fil, default_flow_style=False)
    fil.close()
    return {'exit_status': 1, 'message': "Data successfully dumped"}


def load_config(path):
    try:
        with open(path, 'r') as stream:
            try:
                data = yaml.load(stream)
                # probably need to change this to safeload
                print(data)
                return {'exit_status': 1,
                        'message': "Successfully loaded file", 'data': data}
            except yaml.YAMLError as err:
                return {'exit_status': 0, 'message': "Unable to load file",
                        'error': err}
    except:
        return {'exit_status': 0,
                'message': "You do not have permissions to read " + path +
                           ", or the file does not exist",
                'error': sys.exc_info()}
