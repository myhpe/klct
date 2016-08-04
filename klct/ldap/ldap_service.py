import os
import ssl
import subprocess
import socket
import sys
import logging
from collections import OrderedDict

import ldap3
import yaml
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPStartTLSError

import klct.log.logger

LOG = logging.getLogger(__name__)

class NetworkValidator:
    def _check_valid_ip(self, host_name):
        """
        Checks if the given hostName is a valid IP address.
        Return 1 if valid, 0 if invalid.
        """
        try:
            socket.inet_aton(host_name)
            LOG.debug("Valid IP/Host Name entered")
            return 1
        except socket.error:
            pass
        try:
            socket.inet_pton(socket.AF_INET6, host_name)
            LOG.debug("Valid IPv6 address entered")
            return 1
        except socket.error:
            LOG.warning("Invalid IP/Host Name entered")
            return 0

    def ping_ldap_server(self, host_name):
        """
        Checks if the given hostName is valid, and pings it.
        """
        LOG.info("Initializing ping sequence to " + host_name)
        ret_vals = {'exit_status': 0, 'host_name': host_name, 'message': None}
        new_host_name = ""
        try:
            new_host_name = socket.gethostbyname(host_name)
            LOG.debug("Converted " + host_name + " to an ip: " + new_host_name)
        except socket.gaierror:
            LOG.warning("Unable to convert " + host_name)
            pass

        is_valid = self._check_valid_ip(new_host_name)
        if not is_valid or host_name == "":
            ret_vals['message'] = host_name + " is an invalid host name"
            return ret_vals

        with open(os.devnull, "w"):
            try:
                subprocess.check_output(["ping", "-c", "1", host_name], stderr=subprocess.STDOUT, universal_newlines=True)
                LOG.debug("Successfully pinged " + host_name)
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


class LdapConnection:
    def connect_ldap_server(self, host_name, port_number, user_name, password, want_tls, tls_cert_path):
        """
        Attempts to connect to the provided hostName and port number, default
        port is 389 if none provided, using the provided user name and pass.
        Note: tls not working
        """
        LOG.info("Initializing connection to \"" + host_name + "\"")
        conn_info = self._setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path)
        # if conn_info['exit_status'] == 1:
        #     conn_info['conn'].unbind() front end will unbind for now
        return conn_info


    def _setup_connection(self, host_name, port_number, user_name, password, want_tls, tls_cert_path):
        """
        Sets up a connection given the parameters.
        Note: unbind the returned connection when finished using socket
        Note: need to find a way to check validation of certificate,
        eg. expiration, etc
        """
        ret_vals = {'exit_status': 0, 'message': None, 'error': None, 'server': None, 'conn': None}
        if port_number is None and want_tls == 'n':
            LOG.debug("tls conection not required, setting default port to 389")
            port_number = 389
        elif port_number is None and want_tls == 'y':
            LOG.debug("tls conection not required, setting default port to 636")
            port_number = 636
        try:
            LOG.debug("Attempting to create server object with port: " + str(port_number) + ", username: " + str(user_name) + ", password: " + str(password) + ", tls_requested: " + want_tls + ", certificate path: " + str(tls_cert_path))
            if want_tls == 'n':
                ret_vals['server'] = Server(host_name, port=port_number, get_info=ALL)
            else:
                LOG.debug("Attempting to create tls object with certificate file: " + tls_cert_path)
                try:
                    subprocess.check_output(["openssl", "x509", "-checkend", "120", "-noout", "-in", tls_cert_path], stderr=subprocess.STDOUT, universal_newlines=True)
                    LOG.debug("Tls certificate is valid")
                except:
                    LOG.warning("Tls certificate has expired or will expire within the next 2 minutes")
                    ret_vals['message'] = "Tls certificate has expired or will expire within the next 2 minutes"
                    return ret_vals

                tls_object = ldap3.Tls(ca_certs_file=tls_cert_path, validate=ssl.CERT_REQUIRED)
                ret_vals['server'] = Server(host_name, port=port_number, use_ssl=True, tls=tls_object, get_info=ALL)
                LOG.debug("Successfully created tls object")
            LOG.debug("Successfully created server object")
            LOG.debug("Attempting to create connection socket")
            ret_vals['conn'] = Connection(ret_vals['server'], user=user_name, password=password)
            LOG.debug("Successfully created socket")
            LOG.debug("Attempting to bind to socket")
            if not ret_vals['conn'].bind():
                LOG.warning("Failed to bind to socket")
                ret_vals['message'] = "Failed to bind to socket (Invalid Log in credentials)"
                return ret_vals
            LOG.debug("Successfully bound to socket")
            if want_tls == 'y':
                LOG.debug("Attempting to start tls on connection")
                ret_vals['conn'].start_tls()
                LOG.debug("Successfully started tls")
            ret_vals['exit_status'] = 1
            ret_vals['message'] = "Successfully connected!"
            LOG.debug(str(ret_vals['message']))
            return ret_vals
        except ldap3.LDAPSocketOpenError as err:
            if port_number != 636 and want_tls == 'y':
                ret_vals['message'] = "Invalid socket: Connecting with TLS may require a different port number."
            else:
                ret_vals['message'] = "Failed to connect due to invalid socket."
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


class LdapService:
    def __init__(self, conn, server):
        self.conn = conn
        self.server = server

    def _create_filter(self, attributes, num_attributes):
        """
        Returns a filter based on the number of attributes we want filtered.
        todo: add more number of attributes (currently only handles 3)
        """
        if num_attributes is 1:
            return '(' + attributes[0] + '=*)'
        elif num_attributes is 2:
            return '(&(objectclass=' + attributes[0] + ')(' + attributes[1] + '=*))'
        elif num_attributes is 3:
            return '(&(&(' + attributes[0] + '=' + attributes[1] + '))(objectclass=' + attributes[2] + ')(' + attributes[3] + '=*))'

    def retrieve_server_info(self):
        """
        Retrieves the information related to the server passed in.
        """
        ret_vals = {'exit_status': 0, 'version': None, 'type': None, 'error': None}
        try:
            LOG.info("Attempting to retrieve server Info")
            assert self.conn.closed is not True
            LOG.debug("Connection socket is open")
            LOG.debug("Creating serverinfo and serverschema files")

            orig_stdout = sys.stdout

            sys.stdout = open("serverinfo.txt", "w+")  # note: doesn't matter
            # that we overwrite serverinfo.txt bc users personal files should
            # never be in this directory
            print(self.server.info)
            sys.stdout.close()

            sys.stdout = open("serverschema.txt", "w+")
            print(self.server.schema)
            sys.stdout.close()

            sys.stdout = orig_stdout

            LOG.debug("Dumping server info and server schema to the respective files")
            # print >>serverinfo, server.info
            # print >>serverschema, server.schema
            LOG.debug("Closing serverinfo and serverschema files")

            LOG.debug("Searching for ldap attributes")
            if self.conn.search('', '(objectclass=*)', ldap3.SEARCH_SCOPE_BASE_OBJECT, attributes=ldap3.ALL_ATTRIBUTES, get_operational_attributes=True) is True and self.conn.entries:
                version = ""
                i = 0
                try:
                    version_result = self.conn.response[0]['attributes']['supportedLDAPVersion']
                    for i in range(len(version_result) - 1):
                        version += str(version_result[i]) + ", "
                    if len(version_result) == 1:
                        version += str(version_result[i])
                    else:
                        version += str(version_result[i + 1])
                    LOG.debug("Found supported ldap versions: " + version)
                except:
                    LOG.warning("Unable to find supported ldap versions")
                    version = "N/A"
                try:
                    server_type = self.conn.response[0]['attributes']['structuralObjectClass']
                    LOG.debug("Found ldap server type: " + server_type)
                except:
                    if str(self.server.info).lower().find("microsoft") != -1 and str(self.server.info).lower().find("active directory") != -1:
                        LOG.debug("Found ldap server type: Active Directory")
                        server_type = "Active Directory"
                    else:
                        LOG.warning("Unable to find ldap server type")
                        server_type = "No server type found. (This usually means the server type is AD)"
                ret_vals['exit_status'] = 1
                ret_vals['version'] = "Supported LDAP Version: " + version
                ret_vals['type'] = "LDAP Server Type: " + server_type
                return ret_vals
        except AssertionError as err:
            ret_vals['error'] = "Connection is closed."
        except:
            ret_vals['error'] = sys.exc_info()
        LOG.warning(ret_vals['error'])
        return ret_vals

    def get_ldap_suffix(self):
        """
        Returns the base dn of the ldap server
        """
        LOG.info("Discovering suffix (base DN) from server information")
        try:
            base_dn = str(self.server.info.naming_contexts[0])
            LOG.debug("Found suffix (base DN): " + base_dn)
            return {'exit_status': 1, 'base_dn': base_dn}
        except:
            LOG.warning("Unable to find suffix (base DN)")
            return {'exit_status': 0, 'error': sys.exc_info}

    def check_ldap_suffix(self, base_dn):
        """
        Checks that the given base_dn is the correct suffix for the given
        connection.
        """
        LOG.info("Validating given base suffix (base DN): " + base_dn)
        try:
            assert self.conn.closed is not True
            LOG.debug("Connection is open")
            search_filter = self._create_filter(['cn'], 1)
            LOG.debug("Created search filter: " + search_filter)
            if self.conn.search(search_base=base_dn, search_filter=search_filter) is True and self.conn.entries:
                LOG.debug(base_dn + " is a valid suffix (base DN)")
                return {'exit_status': 1, 'message': base_dn + " is a valid suffix (base DN)"}
            else:
                LOG.warning(base_dn + " is an invalid suffix (base DN)")
        except AssertionError as err:
            LOG.warning("Connection is closed.")
            return {'exit_status': 0, 'message': "Connection is closed", 'error': err}
        except:
            LOG.warning(sys.exc_info())
        return {'exit_status': 0, 'message': base_dn + " is an invalid suffix (base DN)", 'error': sys.exc_info()}

    def validate_info(self, dn, id_attribute, name_attribute):
        """
        Checks that the given dn is valid. If so, it will validate the
        id_attribute and name_attribute as well.
        """
        LOG.info("Validating given DN: " + dn)
        ret_vals = {'exit_status': 1, 'message': None, 'error': None}
        try:
            assert self.conn.closed is not True
            LOG.debug("Connection is open")

            if self.conn.search(search_base=dn, search_scope=ldap3.LEVEL, search_filter='(objectclass=*)', attributes=[ldap3.ALL_ATTRIBUTES], size_limit=1) is True and self.conn.entries:
                LOG.debug(dn + " is a valid DN")
                if id_attribute in self.conn.entries[0]:
                    LOG.debug(id_attribute + " is a valid id attribute")
                else:
                    LOG.warning(id_attribute + " is an invalid id attribute")
                    ret_vals['exit_status'] = 0
                    ret_vals['message'] = id_attribute + " is an invalid id attribute"
                if name_attribute in self.conn.entries[0]:
                    LOG.debug(name_attribute + " is a valid name attribute")
                else:
                    LOG.warning(name_attribute + " is an invalid name attribute")
                    ret_vals['exit_status'] = 0
                    if ret_vals['message'] is None:
                        ret_vals['message'] = name_attribute + " is an invalid name attribute"
                    else:
                        ret_vals['message'] += ", " + name_attribute + " is an invalid name attribute"
                if ret_vals['exit_status'] == 1:
                    ret_vals['message'] = dn + ", " + id_attribute + ", and " + name_attribute + " are valid"
                return ret_vals
        except AssertionError as err:
            LOG.warning("Connection is closed.")
            return {'exit_status': 0, 'message': "Connection is closed", 'error': err}
        except:
            LOG.warning(sys.exc_info())
        return {'exit_status': 0, 'message': dn + " is an invalid DN", 'error': sys.exc_info()}

    def list_object_classes(self, dn, id_attribute):
        """
        Returns a list of the object classes.
        """
        LOG.info("Searching for object classes")
        try:
            assert self.conn.closed is not True
            LOG.debug("Connection is open")
            search_filter = self._create_filter([id_attribute], 1)
            LOG.debug("Created search filter: " + search_filter)
            if self.conn.search(search_base=dn, search_scope=ldap3.LEVEL, search_filter=search_filter, attributes=['objectclass']) is True and self.conn.entries:
                objclasses_list = []
                for objclass_list in self.conn.entries:
                    for objclass in objclass_list.objectclass:
                        if objclass not in objclasses_list:
                            objclasses_list.append(objclass)
                LOG.debug("Found object classes: " + str(objclasses_list))
                return {'exit_status': 1, 'objectclasses': objclasses_list}
            else:
                LOG.warning("No object classes found")
        except AssertionError as err:
            LOG.warning("Connection is closed.")
            return {'exit_status': 0, 'objectclasses': None, 'error': err}
        except:
            LOG.warning(sys.exc_info())
        return {'exit_status': 0, 'objectclasses': None, 'error': sys.exc_info()}

    def validate_object_class(self, dn, objectclass):
        LOG.info("Searching for object classes")
        try:
            assert self.conn.closed is not True
            LOG.debug("Connection is open")
            search_filter = '(objectclass=' + objectclass + ')'
            LOG.debug("Created search filter: " + search_filter)
            if self.conn.search(search_base=dn, search_filter=search_filter, size_limit=1) is True and self.conn.entries:
                LOG.debug(objectclass + " is a valid objectclass")
                return {'exit_status': 1, 'message': objectclass + " is a valid  objectclass", 'error': None}
        except AssertionError as err:
            LOG.warning("Connection is closed.")
            return {'exit_status': 0, 'message': "Connection is closed", 'error': err}
        except:
            LOG.warning(sys.exc_info())
        return {'exit_status': 0, 'message': objectclass + " is an invalid objectclass", 'error': sys.exc_info()}

    def list_entries(self, dn, id_attribute, name_attribute, objectclass, limit):
        """
        Lists the entries, up to the limit.
        """
        LOG.info("Searching for a list of users")
        try:
            assert self.conn.closed is not True
            LOG.debug("Connection is open")
            if limit is None:
                LOG.debug("No limit entered, using 3 as default")
                limit = 3
            search_filter = self._create_filter([objectclass, id_attribute], 2)
            LOG.debug("Created search filter: " + search_filter)
            if self.conn.search(search_base=dn, search_scope=ldap3.LEVEL, search_filter=search_filter, attributes=[name_attribute], size_limit=limit) is True and self.conn.entries:
                LOG.debug("Found list of entries: " + str(self.conn.entries))
                return {'exit_status': 1, 'entries': self.conn.entries}
            else:
                LOG.warning("No entries found")
        except AssertionError as err:
            LOG.warning("Connection is closed.")
            return {'exit_status': 0, 'entries': None, 'error': err}
        except:
            LOG.warning(sys.exc_info())
        return {'exit_status': 0, 'entries': None, 'error': sys.exc_info()}

    def get_entry(self, dn, id_attribute, objectclass, name_attribute, name):
        """
        Returns a specific user.
        """
        LOG.info("Searching for entry: " + name)
        try:
            assert self.conn.closed is not True
            LOG.debug("Connection is open")
            search_filter = self._create_filter([name_attribute, name, objectclass, id_attribute], 3)
            LOG.debug("Created search filter: " + search_filter)
            if self.conn.search(search_base=dn, search_filter=search_filter, attributes=[id_attribute, name_attribute]) is True and self.conn.entries:
                if len(self.conn.entries) > 1:
                    LOG.warning("Duplicate entries found for: " + name)
                    return {'exit_status': 0, 'entry': self.conn.entries, 'error': "Duplicate entries found"}
                LOG.debug("Found entry: " + str(self.conn.entries))
                return {'exit_status': 1, 'entry': self.conn.entries}
            else:
                LOG.warning("Entry: " + name + " not found")
        except AssertionError as err:
            LOG.warning("Connection is closed.")
            return {'exit_status': 0, 'entry': None, 'error': err}
        except:
            LOG.warning(sys.exc_info())
        return {'exit_status': 0, 'entry': None, 'error': sys.exc_info()}


class FileValidator:
    def __init__(self, path):
        self.path = path

    def _validate_file_write(self):
        try:
            fil = open(self.path, 'w')
            return {'exit_status': 1, 'file': fil}
        except:
            LOG.warning("Unable to open file: " + self.path)
            LOG.warning(sys.exc_info())
            return {'exit_status': 0, 'message': "Unable to open file specified"}

    def _validate_file_read(self):
        try:
            fil = open(self.path, 'r')
            return {'exit_status': 1, 'file': fil}
        except:
            message = "Unable to open file: " + str(self.path) + " for reading"
            LOG.debug(message)
            return {'exit_status': 0, 'message': message}


class HOSYamlDump:
    def _ordered_dump(self, data, stream=None, Dumper=yaml.Dumper, **kwds):
        class OrderedDumper(Dumper):
            pass

        def _dict_representer(dumper, data):
            return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())

        def _str_representer(dumper, data):
            if len(data.splitlines()) > 1:
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        OrderedDumper.add_representer(OrderedDict, _dict_representer)
        OrderedDumper.add_representer(str, _str_representer)
        return yaml.dump(data, stream, OrderedDumper, **kwds)

    def save_config(self, data, path, name="ad"):
        """
        Saves the passed in dictionary data to the specified file
        """
        if path is None:
            return _ordered_dump(data, path, Dumper=yaml.SafeDumper, default_flow_style=False)
        LOG.info("Saving configuration options to file.")
        f = FileValidator(path)
        conf_ret_vals = f._validate_file_write()
        if conf_ret_vals['exit_status'] == 0:
            return conf_ret_vals

        if 'tls_cacertfile' in data:
            f = FileValidator(data['tls_cacertfile'])
            ret_vals = f._validate_file_read()
            if ret_vals['exit_status'] == 0:
                return ret_vals
            cert = ret_vals['file'].read()
            cert_dict = {'cacert': cert}
            ret_vals['file'].close()
        else:
            cert_dict = {'cacert': """-----BEGIN CERTIFICATE-----\ncertificate appears here\n-----END CERTIFICATE-----"""}

        LOG.debug("Dumping configuration options: " + str(data) + " to file: " + path)
        dmn_dict = OrderedDict([('name', name), ('description', "Dedicated domain for " + name + " users")])
        conf_dict = OrderedDict([('identity', OrderedDict([('driver', "ldap")])), ('ldap', data)])
        od = OrderedDict([('keystone_domainldap_conf', OrderedDict([('cert_settings', cert_dict), ('domain_settings', dmn_dict), ('conf_settings', conf_dict)]))])
        self._ordered_dump(od, conf_ret_vals['file'], Dumper=yaml.SafeDumper, default_flow_style=False)
        conf_ret_vals['file'].close()
        return {'exit_status': 1, 'message': "Data successfully dumped into " + path}