import os
import subprocess
import socket
import sys
import ldap3
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
    Returns a string message indicating success of failure.
    """
    is_valid = check_valid_IP(host_name)
    if not is_valid:
        return "Invalid Hostname Format"
    #response = os.system("ping -c 1 -q " + host_name)
    with open(os.devnull, "wb") as devnull:
        response = subprocess.check_call(["ping", "-c", "1", host_name], stdout=devnull, stderr=subprocess.STDOUT)
    if response == 0:
        return "Successfully pinged " + host_name
    else:
        return "Unsuccessfully pinged " + host_name


def connect_LDAP_server(host_name, port_number, user_name, password):
    """Attempts to connect to the provided hostName, using the provided user name and pass.
    Return a string indicating the success or failure (along with failure reasons) of the connection. 
    Return an exception indicating what went wrong (returns None on success).
    """
    try:
        tl = Tls(local_private_key_file = 'client_private_key.pem', local_certificate_file = 'client_cert.pem', validate = ssl.CERT_REQUIRED, version = ssl.PROTOCOL_TLSv1, ca_certs_file = 'ca_cert.b64')
        server = Server(host_name, port=port_number, tls=tl, use_ssl=True, get_info=ALL)
        print("\nTrying to connect...")
        conn = Connection(server, user=user_name, password=password)
        conn.start_tls()
        if not conn.bind():
            return"bind failed", conn.results
        else:
            conn.unbind()
            return "Successfully connected!", None
    except ldap3.LDAPSocketOpenError as err:
        return "Failed to connect due to invalid socket.", err
    except ldap3.LDAPInvalidPortError as err:
        return "Invalid Port", err
    except AttributeError as err:
        return "Invalid log in info", err
    except ldap3.LDAPPasswordIsMandatoryError as err:
        return "Please enter a password", err
    except:
        return "Failed to connect due to unknown reasons", sys.exc_info()[0]

#def retrieve_server_info(host_name, user_name, password):
#ad vs. openldap, version, etc

