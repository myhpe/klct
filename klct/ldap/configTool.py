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
    Return the connection socket on success
    Return 0 on failure
    Note: unbind the returned connection when finished using socket
    """
    if port_number is None and want_tls=='n':
        port_number = 389
    elif port_number is None and want_tls=='y':
        port_number = 636
    try:
        server = None
        if want_tls == 'n':
            server = Server(host_name, port=port_number, get_info=ALL)
        else:
            tls_object = ldap3.Tls(ca_certs_file=tls_cert_path, validate=ssl.CERT_REQUIRED)
            server = Server(host_name, port=port_number, use_ssl=True, tls=tls_object, get_info=ALL)
        #print("\nTrying to connect...")
        #print(server)
        conn = Connection(server, version=3, user=user_name, password=password, auto_bind=True)
        #print("connection started")
        #conn.open() #bind implies open
        #if not conn.bind():
        #    return 0, "bind failed", conn.results
        if want_tls == 'y':
            #print("starting tls\n")
            #conn.open()
            conn.start_tls()
        #print(conn)
        return conn, "successfully connected", None
    except ldap3.LDAPSocketOpenError as err:
        return 0, "Failed to connect due to invalid socket.", err
    except ldap3.LDAPInvalidPortError as err:
        return 0, "Invalid Port", err
    except AttributeError as err:
        return 0, "Invalid log in info", err
    except ldap3.LDAPPasswordIsMandatoryError as err:
        return 0, "Please enter a password", err
    except:
        return 0, "Failed to connect due to unknown reasons", sys.exc_info()[1]


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
    Note: call new modularized methods
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


def connect_LDAP_server(host_name, port_number, user_name, password, want_tls, tls_cert_path):
    """Attempts to connect to the provided hostName and port number, default port is 389 if none provided, using the provided user name and pass.
    Return a string indicating the success or failure (along with failure reasons) of the connection.
    Return an exception indicating what went wrong (returns None on success).
    Note: tls not working
    """
    conn_info = setup_connection(host_name, port_number, user_name, password, want_tls, tls_cert_path)
    if conn_info[0] == 0:
        return conn_info[0], conn_info[1], conn_info[2]
    else:
        conn_info[0].unbind()
        return 1, "Successfully connected", None

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
 
