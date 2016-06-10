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
          need to implement validation for URLs and IPV6
    """
    try:
        socket.inet_aton(host_name)
        return 1
    except socket.error:
        return 0


def ping_LDAP_server(host_name):
    """Checks if the given hostName is valid, and pings it.
    Returns -1 for invalid ip
    Returns 0 for unsuccessful ping
    Returns 1 for successful ping
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
    Return a string indicating the success or failure (along with failure reasons) of the connection.
    Return an exception indicating what went wrong (returns None on success).
    """
    if port_number is None:
        port_number = 389
    try:
        server = Server(host_name, port=port_number, get_info=ALL)
        conn = Connection(server)
        if not conn.bind():
            return 0, "Bind failed", conn.results
        else:
            conn.unbind()
            return 1, "Successfully connected!", None
    except ldap3.LDAPSocketOpenError as err:
        return 0, "Failed to connect due to invalid socket.", err
    except ldap3.LDAPInvalidPortError as err:
        return 0, "Invalid Port", err
    except:
        return 0, "Failed to connect due to unknown reasons", sys.exc_info()[0]


def connect_LDAP_server(host_name, port_number, user_name, password, tls_cert_path):
    """Attempts to connect to the provided hostName and port number, default port is 389 if none provided, using the provided user name and pass.
    Return a string indicating the success or failure (along with failure reasons) of the connection.
    Return an exception indicating what went wrong (returns None on success).
    """
    if port_number is None:
        port_number = 389
    if not os.path.exists(tls_cert_path):
        return 0, "Invalid tls certificate path", None
    #tl = ldap3.Tls(local_private_key_file='client_private_key.pem', local_certificate_file='ca.pem', validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1, ca_certs_path=tls_cert_path)#ca_certs_file='cacert.b64')
    tl = ldap3.Tls(ca_certs_file=tls_cert_path, validate=ssl.CERT_REQUIRED)
    try:
        server = Server(host_name, port=port_number, use_ssl=False, tls=tl)
        print("\nTrying to connect...")
        #config = ConfigParser.RawConfigParser()
        #basedn = "uid=%s,%s,%s" %(username, )
        #print("basedn:%s" % basedn)
        conn = Connection(server, user=user_name, password=password)
        conn.open()
        print("line:78")
        conn.start_tls()
        print("line:80")
        if not conn.bind():
            return 0, "bind failed", conn.results
        else:
            conn.unbind()
            return 1, "Successfully connected!", None
    except ldap3.LDAPSocketOpenError as err:
        return 0, "Failed to connect due to invalid socket.", err
    except ldap3.LDAPInvalidPortError as err:
        return 0, "Invalid Port", err
    except AttributeError as err:
        return 0, "Invalid log in info", err
    except ldap3.LDAPPasswordIsMandatoryError as err:
        return 0, "Please enter a password", err
    except:
        return 0, "Failed to connect due to unknown reasons", sys.exc_info()[0]

def retrieve_server_info(host_name, user_name, password):
#ad vs. openldap, version, etc
    print("needs to be implemented")


def check_LDAP_suffix():
    print("needs to be implemented")


def list_users():
    print("needs to be implemented")


def get_user():
    print("needs to be implemented")


def list_groups():
    print("needs to be implemented")


def get_group():
    print("needs to be implemented")


def show_config():
    print("needs to be implemented")


def save_config():
    print("needs to be implemented")
 
