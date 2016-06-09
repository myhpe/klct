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
        self.assertEqual(configTool.ping_LDAP_server(self.invalid_host_name), "Invalid Hostname Format")

    def test_ping_good_host_name(self):
        self.assertEqual(configTool.ping_LDAP_server(self.good_host_name), "Successfully pinged " + self.good_host_name)

    def test_ping_bad_host_name(self):
        self.assertEqual(configTool.ping_LDAP_server(self.bad_host_name), "Unsuccessfully pinged " + self.bad_host_name)

    def test_ping_bad_host(self):
        self.assertEqual(configTool.ping_LDAP_server(self.bad_host), "Unsuccessfully pinged " + self.bad_host)

    def test_ping_no_network(self):
        #this test should fail because it tests the local host
        call(["sudo", "ip", "link", "set", "dev", "eth0", "down"])
        self.assertEqual(configTool.ping_LDAP_server(self.good_host_name), "Unsuccessfully pinged " + self.good_host_name)
        call(["sudo", "ip", "link", "set", "dev", "eth0", "up"])

    """connectLDAPserver() tests"""
    def test_connect_invalid_host_name(self):
        self.assertEqal(configTool.connect_LDAP_server(self.invalid_host_name, self.user_name, self.password), "Failed to connect due to invalid socket.")

    def test_connect_bad_host_name(self):
        self.assertEqual(configTool.connect_LDAP_server(self.bad_host_name, self.user_name, self.password), "Failed to connect due to invalid socket.")

    def test_connect_bad_host(self):
        self.assertEqual(configTool.connect_LDAP_server(self.bad_host, self.user_name, self.password), "Failed to connect due to invalid socket.")

    def test_connect_no_network(self):
        #this test should fail because it tests the local host
        call(["sudo", "ip", "link", "set", "dev", "eth0", "down"])
        self.assertEqual(configTool.connect_LDAP_server(self.good_host_name, self.user_name, self.password), "Failed to connect due to invalid socket.")
        call(["sudo", "ip", "link", "set", "dev", "eth0", "up"])

    #def test_connect_bad_port(self):

    def test_connect_good_host_name(self):
        self.assertEqual(configTool.connect_LDAP_server("10.1.56.3", "", ""), "Successfully connected!")

    def test_bad_username(self):
        print("testing bad username")
        self.assertEqual(configTool.connect_LDAP_server("10.1.56.3", self.bad_user_name, self.password), "Invalid log in info")

    def test_bad_password(self):
        print("testing bad password")
        configTool.connect_LDAP_server(self.good_host_name, self.user_name, self.bad_password)

if __name__ == '__main__':
    unittest.main()
