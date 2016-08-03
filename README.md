Keystone-LDAP Configuration Tool - (v0.1.0)

1 Ping LDAP server IP
url
This checks network to LDAP server ip is ok.

2 Check connection to LDAP	
This checks the connection to the LDAP server by ip/hostname and port number.

3 Check connection to LDAP	This checks the connection to the LDAP server by the user account and TLS is ok.
url, user, password, tls
The user account should be the one to be used by keystone-ldap operations.

4 Get sever information

5 Check LDAP suffix	such as dc=openstack, dc=org

6 Show a list of user related object classes

7 Check user tree dn and show a list of users 
Show a list of users by limit (default to 3); allow user to input limit

8 Get a specific user

9 Show a list of group related object classes 

10 Check group tree dn and show a list of groups	
Show a list of groups by limit (default to 3); allow user to input limit

11 Get a specific group

12 Add additional configuration options

13 Show configuration
Show all the configuration options up to this point.

14 Save/Create Configuration File
Yaml format consistent with HLM. This config file can be used by HLM keystone reconfiguration for LDAP domain backend setup.
The user can save the configuration at any point and continue the rest of steps.

15 Log
Log all the input and output messages during the tool run.
The professional service or customer can send us this log file for debug, if any issue encountered.


