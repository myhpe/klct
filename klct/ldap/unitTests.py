import ldap3
import unittest
from subprocess import call
import configTool


class TestConfigTool(unittest.TestCase):
    invalid_host_name = "invalid hostname"
    bad_host_name = "192.168.134.1"
    bad_host = "192.168.122.2"
    good_host_name = "192.168.122.1"
    user_name = "exampleUser"
    password = "temppassword"
    bad_user_name = "not a user"
    bad_password = "wrong password"

    """pingLDAPserver() tests"""
    def test_ping_invalid_host_name(self):
        self.assertEqual(configTool.pingLDAPserver(self.invalid_host_name), "Invalid Hostname")

    def test_ping_good_host_name(self):
        self.assertEqual(configTool.pingLDAPserver(self.good_host_name), "Successfully pinged " + self.good_host_name)

    def test_ping_bad_host_name(self):
        self.assertEqual(configTool.pingLDAPserver(self.bad_host_name), "Unsuccessfully pinged " + self.bad_host_name)

    def test_ping_bad_host(self):
        self.assertEqual(configTool.pingLDAPserver(self.bad_host), "Unsuccessfully pinged " + self.bad_host)

    def test_ping_no_network(self):
        #this test should fail because it tests the local host
        call(["sudo", "ip", "link", "set", "dev", "eth0", "down"])
        self.assertEqual(configTool.pingLDAPserver(self.good_host_name), "Unsuccessfully pinged " + self.good_host_name)
        call(["sudo", "ip", "link", "set", "dev", "eth0", "up"])

    """connectLDAPserver() tests"""
    def test_connect_invalid_host_name(self):
        self.assertRaises(ldap3.LDAPSocketOpenError, configTool.connectLDAPserver, self.invalid_host_name, self.user_name, self.password)

    def test_connect_bad_host_name(self):
        self.assertRaises(ldap3.LDAPSocketOpenError, configTool.connectLDAPserver, self.bad_host_name, self.user_name, self.password)

    def test_connect_bad_host(self):
        self.assertRaises(ldap3.LDAPSocketOpenError, configTool.connectLDAPserver, self.bad_host, self.user_name, self.password)

    def test_connect_no_network(self):
        #this test should fail because it tests the local host
        call(["sudo", "ip", "link", "set", "dev", "eth0", "down"])
        self.assertRaises(ldap3.LDAPSocketOpenError, configTool.connectLDAPserver, self.good_host_name, self.user_name, self.password)
        call(["sudo", "ip", "link", "set", "dev", "eth0", "up"])

    #def test_connect_bad_port(self):

    def test_connect_good_host_name(self):
        self.assertEqual(configTool.connectLDAPserver(self.good_host_name, self.user_name, self.password), "Successfully connected!")

    def test_bad_username(self):
        print("testing bad username")
        configTool.connectLDAPserver(self.good_host_name, self.bad_user_name, self.password)

    def test_bad_password(self):
        print("testing bad password")
        configTool.connectLDAPserver(self.good_host_name, self.user_name, self.bad_password)

if __name__ == '__main__':
    unittest.main()
