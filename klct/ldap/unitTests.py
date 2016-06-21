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
    AD_user_dn = "ou=UsersTest,dc=keystone,dc=cdl,dc=hp,dc=com"
    AD_group_dn = "ou=UsersTest,dc=keystone,dc=cdl,dc=hp,dc=com"
    AD_bad_dn = "dc=cdl,dc=hp,dc=com"
    AD_user_objectclass = "user"
    AD_group_objectclass = "group"
    AD_user_id_attribute = "cn"
    AD_group_id_attribute = "cn"
    AD_user_name_attribute = "sAMAccountName"
    AD_group_name_attribute = "sAMAccountName"

    OpenLdap_server = "10.1.56.3"
    OpenLdap_base_dn = "dc=cdl,dc=hp,dc=com"
    OpenLdap_user_dn = "ou=Users,dc=cdl,dc=hp,dc=com"
    OpenLdap_group_dn = "ou=Groups,dc=cdl,dc=hp,dc=com"
    OpenLdap_bad_dn = "dc=hi,dc=hp,dc=com"
    OpenLdap_user_objectclass = "posixAccount"
    OpenLdap_group_objectclass = "posixGroup"
    OpenLdap_user_id_attribute = "uid"
    OpenLdap_group_id_attribute = "cn"
    OpenLdap_user_name_attribute = "cn"
    OpenLdap_group_name_attribute = "cn"

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

    ad = configTool.setup_connection(AD_server, None, "LdapQuery", "hpcsqa50", 'n', "")
    openLdap = configTool.setup_connection(OpenLdap_server, None, "", "", 'n', "")

    """check_LDAP_suffix tests"""
    def test_check_good_LDAP_suffix(self):
        self.assertEqual(configTool.check_LDAP_suffix(self.ad['conn'], self.AD_base_dn)['exit_status'], 1)

    def test_check_bad_LDAP_suffix(self):
        self.assertEqual(configTool.check_LDAP_suffix(self.ad['conn'], self.AD_bad_dn)['exit_status'], 0)

    """list_user_related_OC tests"""
    def test_list_AD_user_related_OC(self):
        results = configTool.list_user_related_OC(self.ad['conn'], self.AD_user_dn, self.AD_user_id_attribute)
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['objectclasses'], self.AD_user_objectclass)
    
    def test_list_OpenLdap_user_related_OC(self):
        results = configTool.list_user_related_OC(self.openLdap['conn'], self.OpenLdap_user_dn, self.OpenLdap_user_id_attribute)
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['objectclasses'], self.OpenLdap_user_objectclass)
     
    """list_users tests"""
    def test_list_AD_users_5(self):
        results = configTool.list_users(self.ad['conn'], self.AD_user_dn, self.AD_user_id_attribute, self.AD_user_objectclass, 5)
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['users'][0].cn, "testuser1") #AD_user_id_attribute

    def test_list_OpenLdap_users_5(self):
        results = configTool.list_users(self.openLdap['conn'], self.OpenLdap_user_dn, self.OpenLdap_user_id_attribute, self.OpenLdap_user_objectclass, 5)
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['users'][0].uid, "testuser1") #OpenLdap_user_id_attribute

    """get_user tests"""
    def test_get_user_AD(self):
        results = configTool.get_user(self.ad['conn'], self.AD_user_dn, self.AD_user_id_attribute, self.AD_user_objectclass, self.AD_user_name_attribute, "testuser1")
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['user'][0].sAMAccountName, "testuser1") #AD_user_name_attribute

    def test_get_user_OpenLdap(self):
        results = configTool.get_user(self.openLdap['conn'], self.OpenLdap_user_dn, self.OpenLdap_user_id_attribute, self.OpenLdap_user_objectclass, self.OpenLdap_user_name_attribute, "testuser1")
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['user'][0].cn, "testuser1") #OpenLdap_user_name_attribute

    """list_group_related_OC tests"""
    def test_list_AD_group_related_OC(self):
        results = configTool.list_group_related_OC(self.ad['conn'], self.AD_group_dn, self.AD_group_id_attribute)
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['objectclasses'], self.AD_group_objectclass)
    
    def test_list_OpenLdap_group_related_OC(self):
        results = configTool.list_group_related_OC(self.openLdap['conn'], self.OpenLdap_group_dn, self.OpenLdap_group_id_attribute)
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['objectclasses'], self.OpenLdap_group_objectclass)

    """list_group tests"""
    def test_list_AD_groups_5(self):
        results = configTool.list_groups(self.ad['conn'], self.AD_group_dn, self.AD_group_id_attribute, self.AD_group_objectclass, 5)
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['groups'][0].cn, "testgroup1") #AD_group_id_attribute

    def test_list_OpenLdap_groups_5(self):
        results = configTool.list_groups(self.openLdap['conn'], self.OpenLdap_group_dn, self.OpenLdap_group_id_attribute, self.OpenLdap_group_objectclass, 5)
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['groups'][0].cn, "testgroup1") #OpenLdap_group_id_attribute

    """get_group tests"""
    def test_get_group_AD(self):
        results = configTool.get_group(self.ad['conn'], self.AD_group_dn, self.AD_group_id_attribute, self.AD_group_objectclass, self.AD_group_name_attribute, "testgroup1")
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['group'][0].sAMAccountName, "testgroup1") #AD_group_name_attribute

    def test_get_group_OpenLdap(self):
        results = configTool.get_group(self.openLdap['conn'], self.OpenLdap_group_dn, self.OpenLdap_group_id_attribute, self.OpenLdap_group_objectclass, self.OpenLdap_group_name_attribute, "testgroup1")
        self.assertEqual(results['exit_status'], 1)
        self.assertEqual(results['group'][0].cn, "testgroup1") #OpenLdap_group_name_attribute

if __name__ == '__main__':
    unittest.main()
