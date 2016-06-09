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
    bad_port = "invalid_port"

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
        self.assertEqual(configTool.connect_LDAP_server(self.invalid_host_name, None, "", "")[0], "Failed to connect due to invalid socket.")

    def test_connect_bad_host_name(self):
        self.assertEqual(configTool.connect_LDAP_server(self.bad_host_name, None, "", "")[0], "Failed to connect due to invalid socket.")

    def test_connect_bad_host(self):
        self.assertEqual(configTool.connect_LDAP_server(self.bad_host, None, "", "")[0], "Failed to connect due to invalid socket.")

    def test_connect_no_network(self):
        #this test should fail because it tests the local host
        call(["sudo", "ip", "link", "set", "dev", "eth0", "down"])
        self.assertEqual(configTool.connect_LDAP_server(self.good_host_name, None, "", "")[0], "Failed to connect due to invalid socket.")
        call(["sudo", "ip", "link", "set", "dev", "eth0", "up"])

    def test_connect_bad_port(self):
        self.assertEqual(configTool.connect_LDAP_server(self.good_host_name, self.bad_port, "", "")[0], "Invalid Port")

    def test_connect_good_host_name(self):
        self.assertEqual(configTool.connect_LDAP_server(self.good_host_name, None, "", "")[0], "Successfully connected!")

    def test_bad_username(self):
        self.assertEqual(configTool.connect_LDAP_server(self.good_host_name, None, self.bad_user_name, self.password)[0], "Invalid log in info")

    def test_bad_password(self):
        self.assertEqual(configTool.connect_LDAP_server(self.good_host_name, None, self.user_name, self.bad_password)[0], "Invalid log in info")

if __name__ == '__main__':
    unittest.main()
