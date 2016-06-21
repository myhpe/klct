import ldap3
import unittest
from subprocess import call
import configTool


class TestConfigTool(unittest.TestCase):
    invalid_host_name = "invalid hostname"
    bad_host_name = "112.168.134.1"
    bad_host = "192.168.122.2"
    good_host_name = "192.168.122.1"
    user_name = "exampleUser"
    password = "temppassword"
    bad_user_name = "not a user"
    bad_password = "wrong password"
    bad_port = "invalid_port"

    AD_server = "10.1.31.0"
    AD_user = "LdapQuery"
    AD_pass = "hpcsqa50"
    AD_base_dn = "dc=keystone,dc=cdl,dc=hp,dc=com"
    AD_bad_dn = "dc=cdl,dc=hp,dc=com"
    AD_user_objectclass = "user"
    AD_user_id_attribute = "cn"

    OpenLdap_server = "10.1.56.3"
    OpenLdap_base_dn = "dc=cdl,dc=hp,dc=com"
    OpenLdap_bad_dn = "dc=hi,dc=hp,dc=com"
    OpenLdap_user_objectclass = "posixAccount"
    OpenLdap_user_id_attribute = "uid"

    """pingLDAPserver() tests"""
    def test_ping_invalid_host_name(self):
        self.assertEqual(configTool.ping_LDAP_server(self.invalid_host_name), -1)

    def test_ping_good_host_name(self):
        self.assertEqual(configTool.ping_LDAP_server(self.good_host_name), 1)

    def test_ping_bad_host_name(self):
        self.assertEqual(configTool.ping_LDAP_server(self.bad_host_name), 0)

    def test_ping_bad_host(self):
        self.assertEqual(configTool.ping_LDAP_server(self.bad_host), 0)
    """
    def test_ping_no_network(self):
        #this test should fail because it tests the local host
        call(["sudo", "ip", "link", "set", "dev", "eth0", "down"])
        self.assertEqual(configTool.ping_LDAP_server(self.good_host_name), 0)
        call(["sleep", "1"])
        call(["sudo", "ip", "link", "set", "dev", "eth0", "up"])
        call(["sleep", "1"])
    """

    """connect_LDAP_server_basic() tests"""
    def test_connect_invalid_host_name_basic(self):
        self.assertEqual(configTool.connect_LDAP_server_basic(self.invalid_host_name, None)['exit_status'], 0)

    def test_connect_bad_host_name_basic(self):
        self.assertEqual(configTool.connect_LDAP_server_basic(self.bad_host_name, None)['message'], "Failed to connect due to invalid socket.")

    def test_connect_bad_host_basic(self):
        self.assertEqual(configTool.connect_LDAP_server_basic(self.bad_host, None)['message'], "Failed to connect due to invalid socket.")

    def test_connect_bad_port_basic(self):
        self.assertEqual(configTool.connect_LDAP_server_basic(self.good_host_name, self.bad_port)['message'], "Invalid Port")

    def test_connect_good_hostname_basic(self):
        self.assertEqual(configTool.connect_LDAP_server_basic(self.good_host_name, None)['message'], "Successfully connected!")
 
    """connectLDAPserver() tests"""
    def test_connect_invalid_host_name(self):
        self.assertEqual(configTool.connect_LDAP_server(self.invalid_host_name, None, "", "", 'n', "")['message'], "Failed to connect due to invalid socket.")

    def test_connect_bad_host_name(self):
        self.assertEqual(configTool.connect_LDAP_server(self.bad_host_name, None, "", "", 'n', "")['message'], "Failed to connect due to invalid socket.")

    def test_connect_bad_host(self):
        self.assertEqual(configTool.connect_LDAP_server(self.bad_host, None, "", "", 'n', "")['message'], "Failed to connect due to invalid socket.")

    """
    def test_connect_no_network(self):
        #this test should fail because it tests the local host
        call(["sudo", "ip", "link", "set", "dev", "eth0", "down"])
        self.assertEqual(configTool.connect_LDAP_server(self.good_host_name, None, "", "", 'n', "")['message'], "Failed to connect due to invalid socket.")
        call(["sleep", "1"])
        call(["sudo", "ip", "link", "set", "dev", "eth0", "up"])
        call(["sleep", "1"])
    """

    def test_connect_bad_port(self):
        self.assertEqual(configTool.connect_LDAP_server(self.good_host_name, self.bad_port, "", "", 'n', "")['message'], "Invalid Port")

    def test_connect_good_host_name(self):
        self.assertEqual(configTool.connect_LDAP_server(self.good_host_name, None, "", "", 'n', "")['message'], "Successfully connected!")

    def test_bad_username(self):
        self.assertEqual(configTool.connect_LDAP_server(self.AD_server, None, self.bad_user_name, self.AD_pass, 'n', "")['message'], "Invalid log in info")

    def test_bad_password(self):
        self.assertEqual(configTool.connect_LDAP_server(self.AD_server, None, self.AD_user, self.bad_password, 'n', "")['message'], "Invalid log in info")
    
#TODO: add tls tests


    """check_LDAP_suffix tests"""
    def test_check_good_LDAP_suffix(self):
        connection = configTool.setup_connection(self.AD_server, None, "LdapQuery", "hpcsqa50", 'n', "")
        self.assertEqual(configTool.check_LDAP_suffix(connection['conn'], self.AD_base_dn)['exit_status'], 1)
        connection['conn'].unbind()

    def test_check_bad_LDAP_suffix(self):
        connection = configTool.setup_connection(self.AD_server, None, "LdapQuery", "hpcsqa50", 'n', "")
        self.assertEqual(configTool.check_LDAP_suffix(connection['conn'], self.AD_bad_dn)['exit_status'], 0)
        connection['conn'].unbind()

    """list_user_related_OC tests"""
    def test_list_AD_user_related_OC(self):
        connection = configTool.setup_connection(self.AD_server, None, "LdapQuery", "hpcsqa50", 'n', "")
        results = configTool.list_user_related_OC(connection['conn'], self.AD_base_dn, self.AD_user_id_attribute)
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['objectclasses'], self.AD_user_objectclass)
        connection['conn'].unbind()
    
    def test_list_OpenLdap_user_related_OC(self):
        connection = configTool.setup_connection(self.OpenLdap_server, None, "", "", 'n', "")
        results = configTool.list_user_related_OC(connection['conn'], self.OpenLdap_base_dn, self.OpenLdap_user_id_attribute)
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['objectclasses'], self.OpenLdap_user_objectclass)
        connection['conn'].unbind()
    

if __name__ == '__main__':
    unittest.main()
