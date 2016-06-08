import os
import socket
import ldap3
from ldap3 import Server, Connection, ALL


def checkValidIP(hostName):
    """Checks if the given hostName is a valid IP address.
    Return 1 if valid, 0 if invalid
    note: only checks for valid ipv4 IPs
          need to implement validation for URLs and IPV6
    """
    try:
        socket.inet_aton(hostName)
        return 1
    except socket.error:
        return 0


def pingLDAPserver(hostName):
    """Checks if the given hostName is valid, and pings it
    Returns a string message indicating success of failure
    """
    isValid = checkValidIP(hostName)
    if not isValid:
        return "Invalid Hostname"

    print("ping -c 1" + hostName)
    response = os.system("ping -c 1 " + hostName)
    print("response: %d", response)
    if response == 0:
        return "Successfully pinged " + hostName
    else:
        return "Unsuccessfully pinged " + hostName


def connectLDAPserver(hostName, userName, password):
    try:
        server = Server(hostName, get_info=ALL)
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

def retrieveServerInfo(hostName, userName, password)
    connectLDAPserver(hostname, userName, password)
