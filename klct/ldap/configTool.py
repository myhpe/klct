import os
import socket
import ldap3
from ldap3 import Server, Connection, ALL


def check_valid_IP(host_name):
    """Checks if the given hostName is a valid IP address.
    Return 1 if valid, 0 if invalid
    note: only checks for valid ipv4 IPs
          need to implement validation for URLs and IPV6
    """
    try:
        socket.inet_aton(host_name)
        return 1
    except socket.error:
        return 0


def ping_LDAP_server(host_name):
    """Checks if the given hostName is valid, and pings it
    Returns a string message indicating success of failure
    """
    is_valid = check_valid_IP(host_name)
    if not is_valid:
        return "Invalid Hostname Format"

    print("ping -c 1" + host_name)
    response = os.system("ping -c 1 " + host_name)
    print("response: %d", response)
    if response == 0:
        return "Successfully pinged " + host_name
    else:
        return "Unsuccessfully pinged " + host_name


def connect_LDAP_server(host_name, user_name, password):
    try:
        server = Server(host_name, get_info=ALL)
        print("\nTrying to connect...")
        #conn = Connection(server, authentication = ldap3.AUTH_SIMPLE, user=userName, password=password)
        conn = Connection(server)
        if not conn.bind():
            print("bind failed: ", conn.result)
            return conn.result
        else:
            conn.unbind()
            return "Successfully connected!"
    except ldap3.LDAPSocketOpenError as err:
        print("failed to connect")
        print("error: ", err)
        print("error is of type: ", type(err))
        raise
        return err
    except:
        raise
        return "Failed to connect"

def retrieve_server_info(host_name, user_name, password):
    print("temp")
#ad vs. openldap, version, etc
