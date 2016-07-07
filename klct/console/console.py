# -*- coding: utf-8 -*-
import curses
import locale
import os.path
import sys
import yaml

# if __name__ == "__main__" and __package__ is None:
#     parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     os.sys.path.append(parent_dir)
#
#     print("parent_dir: %s", parent_dir)

import ldap.configTool as configTool
import log.log as log

# sys.path.insert(0, '../ldap')
# import configTool


"""SET UP"""
locale.setlocale(locale.LC_ALL, "")  # for unicode support
stdscr = curses.initscr()  # terminal screen
stdscr_dimensions = stdscr.getmaxyx()  # returns tuple (y,x) of current screen resolution
stdscr.keypad(True)  # enables arrow keys and multi-byte sequences e.g.(f1-f12,page up, page down)
stdscr.scrollok(True)
curses.noecho()
start_instruction = "HOS Keystone-LDAP Configuration Tool. Press 'm' to go to the menu."
if curses.has_colors():  # enable coloring
    curses.start_color()
curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_WHITE)
curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(7, curses.COLOR_GREEN, curses.COLOR_WHITE)
stdscr.bkgd(curses.color_pair(1))
"""Configuration File Status Windows, one for box and one for displaying text"""
status_window = stdscr.subwin(stdscr_dimensions[0] - 2, stdscr_dimensions[1] / 4 - 2, 1,
                              stdscr_dimensions[1] - stdscr_dimensions[1]/4 )
status_window.scrollok(True)
status_window_text = stdscr.subwin(stdscr_dimensions[0] - 4, stdscr_dimensions[1] / 4 - 4, 2,
                                   stdscr_dimensions[1] - stdscr_dimensions[1]/4 + 1)
status_window_text.scrollok(True)
"""VARS THAT MIGHT CHANGE DURING EXECUTION OF PROGRAM"""
menu_color = [curses.color_pair(2)] * 14  # number of menu options = 12
menu_options = ["1. Enter/Validate LDAP Server IP",
                "2. Check Connection to LDAP Server",
                "3. Get Server Information",
                "4. Check LDAP Suffix",
                "5. Input User ID Attribute/User Name Attribute",
                "6. Show List of User-Related ObjectClasses",
                "7. Check User Tree DN and Show List of Users",
                "8. Get a Specific User",
                "9. Input Group ID Attribute/Group Name Attribute",
                "10. Show List of Group Related ObjectClasses",
                "11. Check Group Tree DN and Show List of Groups",
                "12. Get Specific Group",
                "13. Add Additional Configuration Options",
                "14. Save/Create Configuration File"]
configuration_dict = {
               }
temp_dict = {
            "url": "none",
            "suffix": "none",
            "query_scope": "none",
            "user_tree_dn": "none",
            "user": "none",
            "password": "none",
            "user_object_class": "none",
            "user_id_attribute": "none",
            "user_name_attribute": "none",
            "group_tree_dn":"none",
            "group_objectclass": "none",
            "group_id_attribute": "none",
            "use_pool": "none",
            "user_enabled_attribute": "none",
            "user_enabled_mask": "none",
            "user_enabled_default": "none",
            "use_tls": "none" }


var_dict = {"conn_info": "none",
            "object_class": "none"}

"""HELPER METHODS"""


def display_list_with_numbers(screen, y, x, list):
    """Elements in list must be string."""
    num_elements = len(list)
    for i in range(num_elements):
        elem_i = str(list[i])
        elem_string = "{i}. {elem}".format(i=i+1, elem=elem_i)
        screen.addstr(y + i, x, elem_string)


def display_list_with_numbers_test(screen, y, x, list):
    """Elements in list must be string."""
    num_elements = len(list)
    for i in range(num_elements):
        elem_i = str(list[i])
        elem_i = elem_i.replace('\n',"")
        # elem_temp = elem_i[index + 1]
        # elem_i[index] = ' '
        elem_string = "{i}. {elem}".format(i=i+1, elem=elem_i)
        screen.addstr(y + i, x, elem_string)


def show_instructions(screen):
    """Displays the starting instructions prior to the menu display."""
    curses.curs_set(0)
    screen_dimensions = screen.getmaxyx()
    screen.clear()
    char_press = 0
    screen.addstr(screen_dimensions[0]/2,
                  screen_dimensions[1]/2 - len(start_instruction)/2, start_instruction, curses.A_BOLD)
    while char_press != ord('m'):
        char_press = screen.getch()
    screen.clear()
    screen.box()
    screen.refresh()
    main_window = screen.subwin(screen_dimensions[0] - 2, screen_dimensions[1] - screen_dimensions[1]/4 - 1, 1, 1)
    main_window.keypad(True)
    main_window.scrollok(True)
    display_menu(main_window, status_window)


def my_raw_input(screen, y, x, prompt_string):
    """Prompt for input from user. Given a (y, x) coordinate,
    will show a prompt at (y + 1, x). Currently only able to
    prompt for 20 chars, but can change later."""
    curses.echo() # so user can see
    curses.curs_set(True)
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    str_input = screen.getstr(y + 1, x + 1, 255)  # 20 = max chars to in string
    curses.noecho()
    curses.curs_set(False)
    return str_input


def my_pw_input(screen, y, x, prompt_string):
    """Prompt for input from user. Given a (y, x) coordinate,
    will show a prompt at (y + 1, x). Will echo characters but as an '*',
    to hide the password's characters from showing on the screen."""
    curses.noecho() # no echoing
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    x_coord = x + 1
    str_input_pos = 0
    c = screen.getch()
    str_input = []
    while c != 10:
        if c < 256:
            str_input.append(chr(c))
            screen.addch(y + 1, x_coord, "*")
            x_coord += 1
            str_input_pos += 1
        c = screen.getch()
        if c in (263, 8, 330):
            if x_coord > x + 1:
                x_coord -= 1
            screen.addch(y + 1, x_coord, " ")
            if str_input_pos > 0:
                str_input_pos -= 1
            if len(str_input) > 0:
                str_input.pop()
    pw_input = ''.join(str_input)
    return pw_input


def prompt_char_input(screen, y, x, prompt_string, list):
    """Prompt for a single character input from user until user gives a char in list.
     Given a (y, x) coordinate, will show a prompt at (y + 1, x)."""
    curses.echo() # no echoing
    curses.curs_set(True)
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    ch_input = screen.getstr(y + 1, x + 1, 1)  # 20 = max chars to in string
    while ch_input not in list:
        screen.addstr(y, x, "                                     ")
        screen.addstr(y + 1, x, "> ")
        screen.addstr(y, x, prompt_string, curses.color_pair(2))
        screen.refresh()
        ch_input = screen.getstr(y + 1, x + 1, 1)
    curses.noecho()
    curses.curs_set(False)
    return ch_input


def my_numb_input(screen, y, x, prompt_string, limit=None):
    curses.echo()
    curses.curs_set(True)
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addstr(y + 1, x, ">            ")
    screen.refresh()
    numb_input = screen.getstr(y + 1, x + 1, 10)
    while not numb_input.isdigit():
        screen.addstr(y, x, "                                                                  ")
        screen.addstr(y + 1, x, ">                                 ")
        screen.addstr(y, x, prompt_string, curses.color_pair(2))
        numb_input = screen.getstr(y + 1, x + 1, 10)
    if limit is not None:
        if int(numb_input) > limit:
            curses.noecho()
            curses.curs_set(False)
            return my_numb_input(screen, y, x, prompt_string, limit)
        else:
            curses.noecho()
            curses.curs_set(False)
            return int(numb_input)
    else:
        curses.noecho()
        curses.curs_set(False)
        return int(numb_input)


def setup_menu_call(screen, title=""):
    """Typically called at start of a menu method.
    Clears screen and returns max y and max x in tuple (max_y, max_x)."""
    screen.clear()
    screen_dims = screen.getmaxyx()
    screen.addstr(screen_dims[0]/2 - 10, screen_dims[1]/2 - len(title)/2, title,
                  curses.color_pair(1) | curses.A_BOLD | curses.A_UNDERLINE | curses.A_STANDOUT)
    return screen_dims


def end_menu_call(screen, current_step):
    screen_dims = screen.getmaxyx()
    command_menu = {1: menu_ping_ldap_ip,
                    2: menu_check_ldap_connection_adv,
                    3: menu_get_server_info,
                    4: menu_check_ldap_suffix,
                    5: menu_input_user_attributes,
                    6: menu_show_list_user_object_classes,
                    7: menu_check_user_tree_dn_show_users,
                    8: menu_get_specific_user,
                    9: menu_input_group_attributes,
                    10: menu_show_list_group_object_classes,
                    11: menu_check_group_tree_dn_show_groups,
                    12: menu_get_specific_group,
                    13: menu_additional_config_options,
                    14: menu_create_config
    }
    screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 28,
                  "Press 'n' for next step, 'r' to retry, or 'm' for menu.", curses.A_BOLD)
    character = screen.getch()
    while character not in (109, 110, 114):
        character = screen.getch()
    if character == 109:  # 109 == m
        display_menu(screen, status_window)
    elif character == 110:  # 114 == r
        command_menu[current_step + 1](screen)
    elif character == 114:
        command_menu[current_step](screen)
    #
    # command_string = "Enter one of the following commands.\n{cmd_one}\n{cmd_two}\n{cmd_three}".format()


def ip_not_exists(screen, screen_dims):
    screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 26,
                  "No valid IP found. Please complete the previous step", curses.A_BOLD | curses.color_pair(3))
    screen.addstr(screen_dims[0] / 2 - 1, screen_dims[1] / 2 - 22,
              "Press p to input ip address, or 'm' for menu", curses.color_pair(5))
    key_press = screen.getch()
    while key_press not in (109, 112):  # 109 == m, 112 == p
        key_press = screen.getch()
    if key_press == 109:
        display_menu(screen, status_window)
    elif key_press == 112:
        menu_ping_ldap_ip(screen)


def basic_ldap_menu_success(screen, conn_info, screen_dims):
    var_dict["conn_info"] = conn_info
    screen.addstr(screen_dims[0] / 2 - 6, screen_dims[1] / 2 - len(conn_info['message']) / 2,
                  conn_info['message'],
                  curses.color_pair(6) | curses.A_BOLD)
    menu_options[1] = u"2. Check Connection to LDAP (URL) ✓"
    menu_color[1] = curses.color_pair(7)
    screen.addstr(screen_dims[0] / 2 - 5, screen_dims[1] / 2 - 25,
                  "Press 'n' to move on to next step, or 'm' for menu.", curses.A_BOLD)
    character = screen.getch()
    while character != 109:
        character = screen.getch()
    if character == 109:  # 109 == m
        display_menu(screen, status_window)


def basic_ldap_menu_fail(screen, conn_info, screen_dims):
    screen.addstr(screen_dims[0] / 2 - 6, screen_dims[1] / 2 - len(conn_info['message']) / 2,
                  conn_info['message'],
                  curses.color_pair(3) | curses.A_BOLD)
    screen.addstr(screen_dims[0] / 2 - 5, screen_dims[1] / 2 - 18,
              "Press 'r' to retry, or 'm' for menu.")
    char = screen.getch()
    while char not in (109, 114):
        char = screen.getch()
    if char == 109:
        display_menu(screen, status_window)
    elif char == 114:
        menu_check_ldap_connection_basic(screen)


def adv_ldap_setup_prompts(screen, max_yx):
    host_ip = configuration_dict["url"]
    temp_str = my_raw_input(screen, max_yx[0] / 2 - 4, max_yx[1] / 2 - 22,
                            "Please enter the port number. Default is 389.")
    while not temp_str.isdigit():
        screen.clear()
        temp_str = my_raw_input(screen, max_yx[0] / 2 - 4, max_yx[1] / 2 - 22,
                                "Input entered is not a valid port number. Please retry.")
    port_numb = int(temp_str)

    userpw_y_or_n = prompt_char_input(screen, max_yx[0] / 2 - 2, max_yx[1] / 2 - 22,
                                      "Does LDAP server require User/Pass? [y/n]", ('y', 'n'))
    if userpw_y_or_n == 'y':
        user_name = my_raw_input(screen, max_yx[0] / 2, max_yx[1] / 2 - 22, "Please input your username.")
        # if want password hidden as "*" change my_raw_input to my_pw_input
        pass_wd = my_raw_input(screen, max_yx[0] / 2 + 2, max_yx[1] / 2 - 22,
                               "Please type your password.")
        tls_y_coord = max_yx[0] / 2 + 4
    else:
        user_name = ""
        pass_wd = ""
        tls_y_coord = max_yx[0] / 2

    tls_y_or_n = prompt_char_input(screen, tls_y_coord, max_yx[1] / 2 - 22,
                                   "Is TLS enabled? Enter [y/n]", ('y', 'n'))
    if tls_y_or_n == 'n':
        tls_cert_path = None
    else:
        tls_cert_path = my_raw_input(screen, max_yx[0] / 2 + 6, max_yx[1] / 2 - 22,
                                     "Please enter the path of the TLS certificate.")
        while not os.path.isfile(tls_cert_path):
            screen.addstr(max_yx[0] / 2 + 6, max_yx[1] / 2 - 22,
                          "                                              ")
            screen.addstr(max_yx[0] / 2 + 7, max_yx[1] / 2 - 22,
                          ">                                              ")
            tls_cert_path = my_raw_input(screen, max_yx[0] / 2 + 6, max_yx[1] / 2 - 22,
                                         "File not found. Please try again.")
    return [host_ip, port_numb, user_name, pass_wd, tls_y_or_n, tls_cert_path]


def adv_ldap_success(screen, conn_info, max_yx, tls_cert_path=0):
    var_dict["conn_info"] = conn_info
    if tls_cert_path != 0:
        configuration_dict["tls_cacertfile"] = tls_cert_path
        show_console_in_status_window()
        screen.refresh()
    screen.addstr(max_yx[0] / 2 - 7, max_yx[1] / 2 - len(conn_info['message']) / 2,
                  conn_info['message'],
                  curses.color_pair(6) | curses.A_BOLD)
    menu_options[1] = u"2. Check Connection to LDAP ✓"
    menu_color[1] = curses.color_pair(7)
    screen.addstr(max_yx[0] / 2 - 6, max_yx[1] / 2 - 25,
                  "Press 'n' to move on to next step, or 'm' for menu.",
                  curses.A_BOLD)
    character = screen.getch()
    while character not in (109, 110):
        character = screen.getch()
    if character == 109:  # 109 == m
        display_menu(screen, status_window)
    elif character == 110:  # 114 == n
        menu_get_server_info(screen)


def adv_ldap_fail(screen, conn_info, max_yx):
    screen.addstr(max_yx[0] / 2 - 7, max_yx[1] / 2 - len(conn_info['message']) / 2,
                  conn_info['message'],
                  curses.color_pair(3) | curses.A_BOLD)

    screen.addstr(max_yx[0] / 2 - 6, max_yx[1] / 2 - 18,
                  "Press 'r' to retry, or 'm' for menu.")
    char = screen.getch()
    while char not in (109, 114):
        char = screen.getch()
    if char == 109:
        display_menu(screen, status_window)
    elif char == 114:
        menu_check_ldap_connection_adv(screen, 1)

def prompt_base_dn(screen):
    screen_dims = setup_menu_call(screen, "Prompt Base Distinguished Name")
    conn_info = var_dict["conn_info"]
    conn = conn_info['conn']
    prompt_str = "Please enter the base dn. (e.g. dc=openstack,dc=org)"
    base_dn = my_raw_input(screen, screen_dims[0] / 2, screen_dims[1] / 2 - len(prompt_str) / 2, prompt_str)
    screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 10, "Validating suffix...",
                  curses.color_pair(5) | curses.A_BOLD)
    screen.refresh()
    results = configTool.check_LDAP_suffix(conn, base_dn)
    screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 10, "                    ")
    if results["exit_status"] == 1:
        configuration_dict["suffix"] = base_dn
        menu_options[3] = u"4. Check LDAP Suffix ✓"
        menu_color[3] = curses.color_pair(7)
        message_color = 6
        show_console_in_status_window()
        screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(results['message']) / 2, results['message'],
                      curses.color_pair(message_color) | curses.A_BOLD)
        screen.addstr(screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 25,
                      "Press 'n' to move on to next step, or 'm' for menu.", curses.A_BOLD)
    else:
        message_color = 3
        screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(results['message']) / 2, results['message'],
                      curses.color_pair(message_color) | curses.A_BOLD)
        screen.addstr(screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 23,
                      "Press 'r' to retry this step, or 'm' for menu.")
        c = screen.getch()
        while c not in (109, 114):
            c = screen.getch()
        if c == 109:
            display_menu(screen, status_window)
        elif c == 114:
            menu_check_ldap_suffix(screen)


"""MAIN METHODS"""


def show_console_in_status_window():
    status_window.box()
    status_window_text.addstr(0, 0, "Keystone-LDAP Configuration", curses.A_BOLD | curses.A_UNDERLINE)
    if bool(configuration_dict):
        configuration_dict_yaml_str = yaml.dump(configuration_dict, stream=None, default_flow_style=False)
        status_window_text.addstr(1, 0, configuration_dict_yaml_str)
    status_window.refresh()
    status_window_text.refresh()


def menu_ping_ldap_ip(screen):
    """Displays a screen prompting user for IP address and then
    pings that IP address to see if it able to send a response."""
    screen_dims = setup_menu_call(screen, "1. Enter/Validate LDAP Server IP")
    success = "Successfully pinged given IP address."
    fail = "Unsuccessfully pinged given IP address."
    prompt_ip_string = "Please Enter the IP Address of the LDAP server."
    ip_string = my_raw_input(screen, screen_dims[0] / 2, screen_dims[1] / 2 - len(prompt_ip_string)/2,
                             prompt_ip_string)
    screen.addstr(screen_dims[0] / 2 - 5, screen_dims[1] / 2 - 12, "Attempting to ping IP...",
                  curses.color_pair(5) | curses.A_BLINK)
    screen.refresh()

    temp_bool = configTool.ping_LDAP_server(ip_string)
    screen.addstr(screen_dims[0] / 2 - 5, screen_dims[1] / 2 - 12, "                        ")
    if temp_bool == 1 and ip_string != "":
        screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - len(success) / 2,
                      success, curses.color_pair(6))
        screen.addstr(screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 26,
                      "This IP will automatically be used in the next steps.", curses.color_pair(4))
        screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 25,
                      "Press 'n' to move on to next step, or 'm' for menu.", curses.A_BOLD)
        menu_options[0] = u"1. Ping LDAP Server IP ✓"
        menu_color[0] = curses.color_pair(7)
        configuration_dict["url"] = "ldap://" + ip_string
        show_console_in_status_window()
    elif temp_bool == -1:
        screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 30,
                      "Invalid Hostname or IP. Press 'r' to retry, or 'm' for menu.", curses.color_pair(3))
    else:
        screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - len(fail) / 2, fail, curses.color_pair(3))
        screen.addstr(screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 23,
                      "Press 'r' to retry this step, or 'm' for menu.")
    temp_char = screen.getch()
    while temp_char not in (110, 109, 114):  # 109 = 'm', 110 = 'n', 114 = 'r'
        temp_char = screen.getch()
    if temp_char == 109:
        display_menu(screen, status_window)
    elif temp_char == 110:
        menu_check_ldap_connection_adv(screen, 1)
    elif temp_char == 114:
        menu_ping_ldap_ip(screen)


def menu_check_ldap_connection_basic(screen):
    """The method that handles the 'Check Connections to LDAP Server' option."""
    screen_dims = setup_menu_call(screen)
    if configuration_dict["url"] == "none":
        ip_not_exists(screen, screen_dims)
    else:
        y_n = prompt_char_input(screen, screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 26,
                                "Valid IP has been found, would you like to use this? [y/n]", ('y', 'n'))
        screen.clear()
        if y_n == 'y':
            host_ip = configuration_dict["url"]
            temp_str = my_raw_input(screen, screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 22,
                                    "Please enter the port number. Default is 389.")
            while not temp_str.isdigit():
                screen.clear()
                temp_str = my_raw_input(screen, screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 30,
                                        "Input entered is not a valid port number. Please retry.")
            port_numb = int(temp_str)
            screen.addstr(screen_dims[0] / 2 - 7, screen_dims[1] / 2 - 18, "Attempting to connect to LDAP server...",
                          curses.color_pair(5))
            screen.refresh()

            conn_info = configTool.connect_LDAP_server_basic(host_ip, port_numb)
            screen.addstr(screen_dims[0] / 2 - 7, screen_dims[1] / 2 - 18, "                                       ")
            if conn_info['exit_status'] == 1:
                basic_ldap_menu_success(screen, conn_info, screen_dims)
            else: # error occurred during ldap ping
                basic_ldap_menu_fail(screen, conn_info, screen_dims)
        else:
            menu_ping_ldap_ip(screen)


def menu_check_ldap_connection_adv(screen, skip=0):
    max_yx = setup_menu_call(screen, "2. Check Connection to LDAP Server")
    if not configuration_dict.has_key("url"):
        ip_not_exists(screen, max_yx)
    else:
        if skip == 0:
            y_n = prompt_char_input(screen, max_yx[0] / 2 - 4, max_yx[1] / 2 - 26,
                                "Valid IP has been found, would you like to use this? [y/n]", ('y', 'n'))
        else:
            y_n = 'y'
        screen.clear()
        if y_n == 'y':
            adv_ldap_inputs = adv_ldap_setup_prompts(screen, max_yx)
            host_ip = adv_ldap_inputs[0]
            port_numb = adv_ldap_inputs[1]
            user_name = adv_ldap_inputs[2]
            pass_wd = adv_ldap_inputs[3]
            tls_y_or_n = adv_ldap_inputs[4]
            tls_cert_path = adv_ldap_inputs[5]
            screen.addstr(max_yx[0] / 2 - 8, max_yx[1] / 2 - 18, "Attempting to connect to LDAP server...",
                          curses.color_pair(5))
            screen.refresh()
            conn_info = configTool.connect_LDAP_server(host_ip, port_numb, user_name, pass_wd, tls_y_or_n,
                                                       tls_cert_path)
            screen.addstr(max_yx[0] / 2 - 8, max_yx[1] / 2 - 18, "                                       ")
            if conn_info['exit_status'] == 1:
                if tls_cert_path != None:
                    adv_ldap_success(screen, conn_info, max_yx, tls_cert_path)
                else:
                    adv_ldap_success(screen, conn_info, max_yx)
            else:  # error occurred during ldap ping
                adv_ldap_fail(screen, conn_info, max_yx)
        else:
            menu_ping_ldap_ip(screen)


def menu_get_server_info(screen):
    """Displays server information on screen.
    Currently only displays version and type, but later will add information."""
    screen_dims = setup_menu_call(screen, "3. Get Server Information")
    if var_dict["conn_info"] == "none":
        error_msg = "No LDAP server found. Press 'm' to go to menu."
        screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - len(error_msg)/2, error_msg,
                      curses.color_pair(3) | curses.A_BOLD)
        screen.getch()
        display_menu(screen, status_window)
    else:
        conn_info = var_dict["conn_info"]
        server = conn_info["server"]
        server_info_dict = configTool.retrieve_server_info(conn_info["conn"], server)
        if server_info_dict["exit_status"] == 1:
            menu_options[2] = u"3. Get Server Information ✓"
            menu_color[2] = curses.color_pair(7)
            version = str(server_info_dict["version"])
            ldap_type = str(server_info_dict["type"])
            strlen = len(ldap_type)
            if len(version) > len(ldap_type):
                strlen = len(version)
            screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - strlen/2, version, curses.color_pair(5))
            screen.addstr(screen_dims[0] / 2 + 1, screen_dims[1] / 2 - strlen/2, ldap_type, curses.color_pair(5))
            screen.refresh()
        else:
            screen.addstr(screen_dims[0]/2 + 1, screen_dims[1]/2, "error", curses.color_pair(3))

        screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 10, "Server Information:", curses.A_BOLD)
        screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 25,
                      "Press 'n' to move on to next step, or 'm' for menu.", curses.A_BOLD)
        c = screen.getch()
        while c not in (109, 110):
            c = screen.getch()
        if c == 109:
            display_menu(screen, status_window)
        if c == 110:
            menu_check_ldap_suffix(screen)


def menu_check_ldap_suffix(screen):
    """If failure, may be due to invalid credentials. May want to alert user of this later on."""
    screen_dims = setup_menu_call(screen, "4. Check LDAP Suffix")
    if var_dict["conn_info"] == "none":
        screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - 23, "No LDAP server found. Press 'm' to go to menu.")
        screen.getch()
        display_menu(screen, status_window)
    else:
        screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - 9, "Fetching base dn...", curses.color_pair(5))
        server = var_dict["conn_info"]["server"]
        ret_vals = configTool.get_LDAP_suffix(server)
        screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - 9, "                   ")
        if ret_vals["exit_status"] == 0:
            screen.addstr(screen_dims[0] / 2 + 1, screen_dims[1] / 2 - 23, "Unable to find base dn, Please input a base dn")
            prompt_base_dn(screen)
        elif ret_vals["exit_status"] == 1:
            base_dn = ret_vals['base_dn']
            configuration_dict["suffix"] = base_dn
            menu_options[3] = u"4. Check LDAP Suffix ✓"
            menu_color[3] = curses.color_pair(7)
            show_console_in_status_window()
            screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - (len(base_dn) - 8), base_dn + " is your base dn.")
            y_n = prompt_char_input(screen, screen_dims[0] / 2 + 2, screen_dims[1] / 2 - 17,
                                    "Is this information correct? [y/n]", ('y', 'n'))
            if y_n == 'y':
                screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 25, "Press 'n' to move on to next step, or 'm' for menu.", curses.A_BOLD)
            else:
                prompt_base_dn(screen)

        c = screen.getch()
        while c not in (109, 110):
            c = screen.getch()
        if c == 109:
            display_menu(screen, status_window)
        elif c == 110:
            menu_input_user_attributes(screen)


        #base_dn = my_raw_input(screen, screen_dims[0]/2, screen_dims[1]/2 - len(prompt_str)/2, prompt_str)
        #screen.addstr(screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 10, "Validating suffix...",
        #              curses.color_pair(5) | curses.A_BOLD)
        # screen.refresh()
        # results = configTool.check_LDAP_suffix(conn, base_dn)
        # if results["exit_status"] == 1:
        #     configuration_dict["suffix"] = base_dn
        #     menu_options[3] = u"4. Check LDAP Suffix ✓"
        #     menu_color[3] = curses.color_pair(7)
        #     message_color = 6
        #     show_console_in_status_window()
        #     screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(results['message']) / 2, results['message'],
        #                   curses.color_pair(message_color) | curses.A_BOLD)
        #     screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 25,
        #                   "Press 'n' to move on to next step, or 'm' for menu.", curses.A_BOLD)
        #     c = screen.getch()
        #     while c not in (109, 110):
        #         c = screen.getch()
        #     if c == 109:
        #         display_menu(screen, status_window)
        #     elif c == 110:
        #         menu_input_user_attributes(screen)
        # else:
        #     message_color = 3
        #     screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(results['message']) / 2, results['message'],
        #                   curses.color_pair(message_color) | curses.A_BOLD)
        #     screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 23,
        #                   "Press 'r' to retry this step, or 'm' for menu.")
        #     c = screen.getch()
        #     while c not in (109, 114):
        #         c = screen.getch()
        #     if c == 109:
        #         display_menu(screen, status_window)
        #     elif c == 114:
        #         menu_check_ldap_suffix(screen)


def menu_input_user_attributes(screen):
    screen_dims = setup_menu_call(screen, "5. Input User ID Attribute/User Name Attribute")
    # IMPLEMENT ME
    user_id_attr_prompt = "What is the user id attribute?"
    user_name_attr_prompt = "What is the user name attribute?"
    user_tree_dn_prompt = "What is the user tree DN, not including the base DN (e.g. ou=Users)?"
    alt_user_tree_dn_prompt = "What is the user tree DN, including the base DN (e.g. ou=Users,dc=hp,dc=com)"

    user_id_attribute = my_raw_input(screen, screen_dims[0] / 2, screen_dims[1] / 2 - len(user_tree_dn_prompt)/2,
                                     user_id_attr_prompt)
    configuration_dict["user_id_attribute"] = user_id_attribute
    show_console_in_status_window()

    user_name_attribute = my_raw_input(screen, screen_dims[0] / 2 + 2, screen_dims[1] / 2 - len(user_tree_dn_prompt)/2,
                                       user_name_attr_prompt)
    configuration_dict["user_name_attribute"] = user_name_attribute # VALIDATE INPUT?
    show_console_in_status_window()
    if configuration_dict.has_key("suffix"):
        user_tree_dn = my_raw_input(screen, screen_dims[0] / 2 + 4, screen_dims[1] / 2 - len(user_tree_dn_prompt)/2,
                                         user_tree_dn_prompt)
        configuration_dict["user_tree_dn"] = user_tree_dn + "," + configuration_dict["suffix"]
        show_console_in_status_window()
    else:
        user_tree_dn = my_raw_input(screen, screen_dims[0] / 2 + 4, screen_dims[1] / 2 - len(user_tree_dn_prompt) / 2,
                                    user_tree_dn_prompt)
        configuration_dict["user_tree_dn"] = user_tree_dn + "," + configuration_dict["suffix"]
        show_console_in_status_window()
    menu_options[4] = u"5. Input User ID Attribute/User Name Attribute ✓"
    menu_color[4] = curses.color_pair(7)

    end_menu_call(screen, 5)


def validate_user_dn_input(string):
    """Validate user tree dn?
    Check to see that ou= is not put in prefix, and no comma at end?"""
    pass


def menu_show_list_user_object_classes(screen):
    screen_dims = setup_menu_call(screen, "6. Show List of User-Related ObjectClasses")
    screen.refresh()
    if var_dict["conn_info"] == "none" or not configuration_dict.has_key("suffix"):
        prompt_string = "No connection to server found or no suffix. Press 'm' to go to menu."
        screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - len(prompt_string)/2, prompt_string,
                      curses.color_pair(3) | curses.A_BOLD)
        screen.getch()
        display_menu(screen, status_window)
    else:
        retrieving_string = "Retrieving list of object classes..."
        blnk_retrieve_str = "                                    "
        screen.addstr(screen_dims[0]/2 - 2, screen_dims[1]/2 - len(retrieving_string)/2, retrieving_string,
                      curses.color_pair(5))
        screen.refresh()
        conn_info = var_dict["conn_info"]
        conn = conn_info['conn']
        base_dn = configuration_dict["suffix"]
        if configuration_dict.has_key("user_id_attribute"):
            user_id_attribute = configuration_dict["user_id_attribute"]
            return_values = configTool.list_user_related_OC(conn, configuration_dict["user_tree_dn"], user_id_attribute)
            screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(blnk_retrieve_str) / 2, blnk_retrieve_str)
            if return_values['exit_status'] == 1:
                menu_options[5] = u"6. Show List of User-Related ObjectClasses ✓"
                menu_color[5] = curses.color_pair(7)
                screen.addstr(screen_dims[0] / 2 - 1, screen_dims[1] / 2 - 15, "User Object classes:")
                object_classes_list = return_values['objectclasses'] + ["None of the above"]
                display_list_with_numbers(screen, screen_dims[0]/2, screen_dims[1]/2 - 15, object_classes_list)
                num_obj_classes = len(object_classes_list)
                choice = my_numb_input(screen, screen_dims[0]/2 + num_obj_classes, screen_dims[1]/2 - 15,
                                       "Please choose a number.", num_obj_classes)
                if choice == num_obj_classes:
                    usr_obj_class = my_raw_input(screen, screen_dims[0]/2 + num_obj_classes + 2, screen_dims[1]/2 - 15,
                                                 "Please enter the user object class")
                else:
                    usr_obj_class = object_classes_list[choice - 1]
                configuration_dict["user_object_class"] = usr_obj_class
                screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 23, "Press 'n' for next, or 'm' to go to the menu.",
                              curses.A_BOLD)
                show_console_in_status_window()
            else:
                # ERROR OCCURED
                screen.addstr(screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 12, "No object classes found.")
                screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - 24,
                              "Press 'r' to re-enter user info, or 'm' for menu.")
                c = screen.getch()
                while c not in (109, 114):
                    c = screen.getch()
                if c == 109:
                    display_menu(screen, status_window)
                elif c == 114:
                    menu_input_user_attributes(screen)
        else:
            screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(blnk_retrieve_str) / 2, blnk_retrieve_str)
            error_prompt = "Please input the user id attribute in step 5."
            screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - len(error_prompt) / 2, error_prompt,
                          curses.color_pair(3) | curses.A_BOLD)
            screen.addstr(screen_dims[0] / 2 - 5, screen_dims[1] / 2 - 14, "Press 'm' to go to the menu.",
                          curses.A_BOLD)
        c = screen.getch()
        while c not in (109, 110):
            c = screen.getch()
        if c == 109:
            display_menu(screen, status_window)
        elif c == 110:
            menu_check_user_tree_dn_show_users(screen)


def check_user_config_dict(screen, screen_dims):
    if var_dict["conn_info"] == "none":
        no_conn_info_msg = "No LDAP server found. Please complete steps 1 and 2."
        screen.addstr(screen_dims[0]/2, screen_dims[1]/2 - len(no_conn_info_msg)/2, no_conn_info_msg,
                      curses.color_pair(3) | curses.A_BOLD)
        if not configuration_dict.has_key("user_tree_dn") or not configuration_dict.has_key(
                "user_id_attribute") or not configuration_dict.has_key("user_object_class"):
            no_user_info_msg = "Could not find user attribute information. Please complete step 5."
            screen.addstr(screen_dims[0] / 2 + 2, screen_dims[1] / 2 - len(no_user_info_msg)/2, no_user_info_msg,
                          curses.color_pair(3) | curses.A_BOLD)
        return False
    if not configuration_dict.has_key("user_tree_dn") or not configuration_dict.has_key("user_id_attribute") or not configuration_dict.has_key("user_object_class"):
        no_user_info_msg = ""
        screen.addstr(screen_dims[0]/2 + 2, screen_dims[1]/2 - len(no_user_info_msg), no_user_info_msg,
                      curses.color_pair(3) | curses.A_BOLD)
        return False
    return True


def menu_check_user_tree_dn_show_users(screen):
    screen_dims = setup_menu_call(screen, "7. Check User Tree DN and Show List of Users")
    if check_user_config_dict(screen, screen_dims):
        conn = var_dict["conn_info"]["conn"]
        user_tree_dn = configuration_dict["user_tree_dn"]
        user_id_attribute = configuration_dict["user_id_attribute"]
        object_class = configuration_dict["user_object_class"]
        limit_prompt = "How many users would you like to see?"
        limit = my_numb_input(screen, screen_dims[0]/2 - 2, screen_dims[1]/8, limit_prompt)
        return_values = configTool.list_users(conn, user_tree_dn, user_id_attribute, object_class, limit)
    else :
        return_values = {"exit_status": 0}
    if return_values["exit_status"] == 1:
        menu_options[6] = u"7. Check User Tree DN and Show List of Users ✓"
        menu_color[6] = curses.color_pair(7)
        list_of_users = return_values["users"]
        display_list_with_numbers_test(screen, screen_dims[0]/2, screen_dims[1]/8, list_of_users)
        screen.refresh()
        end_menu_call(screen, 7)
    else:
        err_msg = "Unable to retrieve users"
        screen.addstr(screen_dims[0]/2 - 2, screen_dims[1]/2 - len(err_msg)/2, err_msg, curses.color_pair(3)| curses.A_BOLD)
        end_menu_call(screen, 7)


def menu_get_specific_user(screen):
    screen_dims = setup_menu_call(screen, "8. Get a Specific User")
    if check_user_config_dict(screen, screen_dims):
        conn = var_dict["conn_info"]["conn"]
        user_dn = configuration_dict["user_tree_dn"]
        user_id_attribute = configuration_dict["user_id_attribute"]
        object_class = configuration_dict["user_object_class"]
        user_name_attribute = configuration_dict["user_name_attribute"] # ? where does this come from
        name_msg_prompt = "What is the user name you would like to get?"
        name = my_raw_input(screen, screen_dims[0]/2 - 2, screen_dims[1]/2 - len(name_msg_prompt), name_msg_prompt)
        return_values = configTool.get_user(conn, user_dn, user_id_attribute, object_class, user_name_attribute, name)
    else:
        return_values = {"exit_status": 0}
    if return_values["exit_status"] == 1:
        menu_options[7] = u"8. Get a Specific User ✓"
        menu_color[7] = curses.color_pair(7)
        user = return_values["user"]
        display_list_with_numbers(screen, screen_dims[0] / 2, screen_dims[1] / 2 - 8, user)
        end_menu_call(screen, 8)
    else:
        err_msg = "Unable to retrieve user"
        screen.addstr(screen_dims[0]/2 - 2, screen_dims[1]/2 - len(err_msg)/2, err_msg, curses.color_pair(3)| curses.A_BOLD)
        end_menu_call(screen, 8)


def menu_input_group_attributes(screen):
    screen_dims = setup_menu_call(screen, "9. Input Group ID Attribute/Group Name Attribute")
    group_id_attr_prompt = "What is the group id attribute?"
    group_name_attr_prompt = "What is the group name attribute?"
    group_tree_dn_prompt = "What is the group tree DN, not including the base DN (e.g. ou=Groups)?"
    alt_group_tree_dn_prompt = "What is the group tree DN, including the base DN (e.g. ou=Groups,dc=hp,dc=com)?"
    group_id_attribute = my_raw_input(screen, screen_dims[0] / 2, screen_dims[1] / 2 - len(group_tree_dn_prompt) / 2,
                                     group_id_attr_prompt)
    configuration_dict["group_id_attribute"] = group_id_attribute
    show_console_in_status_window()
    group_name_attribute = my_raw_input(screen, screen_dims[0] / 2 + 2,
                                       screen_dims[1] / 2 - len(group_tree_dn_prompt) / 2,
                                       group_name_attr_prompt)
    configuration_dict["group_name_attribute"] = group_name_attribute  # VALIDATE INPUT?
    show_console_in_status_window()
    if configuration_dict.has_key("suffix"):
        group_tree_dn = my_raw_input(screen, screen_dims[0] / 2 + 4, screen_dims[1] / 2 - len(group_tree_dn_prompt) / 2,
                                     group_tree_dn_prompt)
        configuration_dict["group_tree_dn"] = group_tree_dn + "," + configuration_dict["suffix"]
        show_console_in_status_window()
    else:
        group_tree_dn = my_raw_input(screen, screen_dims[0] / 2 + 4, screen_dims[1] / 2 - len(alt_group_tree_dn_prompt) / 2,
                                     alt_group_tree_dn_prompt)
        configuration_dict["group_tree_dn"] = group_tree_dn + "," + configuration_dict["suffix"]
        show_console_in_status_window()
    menu_options[8] = u"9. Input Group ID Attribute/Group Name Attribute ✓"
    menu_color[8] = curses.color_pair(7)
    screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 25,
                  "Press 'n' to move on to next step, or 'm' for menu.", curses.A_BOLD)
    end_menu_call(screen, 9)


def check_group_config_dict(screen, screen_dims):
    if var_dict["conn_info"] == "none":
        no_conn_info_msg = "No LDAP server found. Please complete steps 1 and 2."
        screen.addstr(screen_dims[0]/2, screen_dims[1]/2 - len(no_conn_info_msg)/2, no_conn_info_msg,
                      curses.color_pair(3) | curses.A_BOLD)
        if not configuration_dict.has_key("group_tree_dn") or not configuration_dict.has_key(
                "group_id_attribute") or not configuration_dict.has_key("group_object_class"):
            no_user_info_msg = "Could not find group attribute information. Please complete step 5."
            screen.addstr(screen_dims[0] / 2 + 2, screen_dims[1] / 2 - len(no_user_info_msg)/2, no_user_info_msg,
                          curses.color_pair(3) | curses.A_BOLD)
        return False
    if not configuration_dict.has_key("group_tree_dn") \
            or not configuration_dict.has_key("group_id_attribute")\
            or not configuration_dict.has_key("group_object_class"):
        no_user_info_msg = ""
        screen.addstr(screen_dims[0]/2 + 2, screen_dims[1]/2 - len(no_user_info_msg), no_user_info_msg,
                      curses.color_pair(3) | curses.A_BOLD)
        return False
    return True


def menu_show_list_group_object_classes(screen):
    screen_dims = setup_menu_call(screen, "10. Show List of Group Related ObjectClasses")
    if check_group_config_dict(screen, screen_dims):
        conn = var_dict["conn_info"]["conn"]
        group_dn = configuration_dict["group_tree_dn"]
        group_id_attribute = configuration_dict["group_id_attribute"]
        return_values = configTool.list_group_related_OC(conn, group_dn, group_id_attribute)
    else:
        return_values = {"exit_status": 0}
    if return_values["exit_status"] == 1:
        object_classes_list = return_values['objectclasses']
        display_list_with_numbers(screen, screen_dims[0] / 2, screen_dims[1] / 2 - 15, object_classes_list)
        num_obj_classes = len(object_classes_list)
        choice = my_numb_input(screen, screen_dims[0] / 2 + num_obj_classes, screen_dims[1] / 2 - 15,
                               "Please choose one of the above.", num_obj_classes)
        configuration_dict["group_object_class"] = object_classes_list[choice - 1]
        show_console_in_status_window()
        menu_options[9] = u"10. Show List of Group Related ObjectClasses ✓"
        menu_color[9] = curses.color_pair(7)
        end_menu_call(screen, 10)
    else:
        err_msg = "Unable to retrieve group object classes"
        screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(err_msg) / 2, err_msg,
                      curses.color_pair(3) | curses.A_BOLD)
        end_menu_call(screen, 10)


def menu_check_group_tree_dn_show_groups(screen):
    screen_dims = setup_menu_call(screen, "11. Check Group Tree DN and Show List of Groups")
    if check_group_config_dict(screen, screen_dims):
        conn = var_dict["conn_info"]["conn"]
        group_dn = configuration_dict["group_tree_dn"]
        group_id_attribute = configuration_dict["group_id_attribute"]
        object_class = configuration_dict["group_object_class"]
        limit_prompt = "How many groups would you like to see?"
        limit = my_numb_input(screen, screen_dims[0]/2 - 2, screen_dims[1]/2 - len(limit_prompt)/2, limit_prompt)
        return_values = configTool.list_groups(conn, group_dn, group_id_attribute, object_class, limit)
    else:
        return_values = {"exit_status": 0}
    if return_values["exit_status"] == 1:
        menu_options[9] = u"11. Check Group Tree DN and Show List of Groups ✓"
        menu_color[9] = curses.color_pair(7)
        list_of_groups = return_values["groups"]
        display_list_with_numbers(screen, screen_dims[0] / 2, screen_dims[1]/4, list_of_groups)
        end_menu_call(screen, 11)
    else:
        err_msg = "Unable to retrieve groups"
        screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(err_msg) / 2, err_msg,
                      curses.color_pair(3) | curses.A_BOLD)
        end_menu_call(screen, 11)


def menu_get_specific_group(screen):
    screen_dims = setup_menu_call(screen, "12. Get Specific Group")
    if check_group_config_dict(screen, screen_dims):
        conn = var_dict["conn_info"]["conn"]
        group_dn = configuration_dict["group_tree_dn"]
        group_id_attribute = configuration_dict["group_id_attribute"]
        object_class = configuration_dict["group_object_class"]
        group_name_attribute = configuration_dict["group_name_attribute"]
        name_msg_prompt = "What is the group name you would like to get?"
        name = my_raw_input(screen, screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(name_msg_prompt), name_msg_prompt)
        return_values = configTool.get_group(conn, group_dn, group_id_attribute,
                                             object_class, group_name_attribute, name)
    else:
        return_values = {"exit_status": 0}
    if return_values["exit_status"] == 1:
        groups = return_values["group"]
        display_list_with_numbers(screen, screen_dims[0]/2, screen_dims[1]/4, groups)
        menu_options[10] = u"12. Get Specific Group ✓"
        menu_color[10] = curses.color_pair(7)
        end_menu_call(screen, 12)
    else:
        err_msg = "Unable to retrieve group"
        screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - len(err_msg) / 2, err_msg,
                      curses.color_pair(3) | curses.A_BOLD)
        end_menu_call(screen, 12)


def menu_additional_config_options(screen):
    screen_dims = setup_menu_call(screen, "13. Add Additional Configuration Options")
    use_pool_prompt = "What is use_pool? (e.g. True/False)"
    user_enabled_attribute_prompt = "What is user_enabled_attribute? (e.g. userAccountControl)"
    user_enabled_mask_prompt = "What is user_enabled_mask? (e.g. 2)"
    user_enabled_default_prompt = "What is user_enabled_default? (e.g. 512)"
    configuration_dict["use_pool"] = my_raw_input(screen, screen_dims[0]/2 - 2,
                                                  screen_dims[1]/2 - len(use_pool_prompt)/2, use_pool_prompt)
    show_console_in_status_window()
    configuration_dict["user_enabled_attribute"] = my_raw_input(screen, screen_dims[0] / 2,
                                                                screen_dims[1] / 2 - len(
                                                                    user_enabled_attribute_prompt) / 2,
                                                                user_enabled_attribute_prompt)
    show_console_in_status_window()
    configuration_dict["user_enabled_mask"] = my_numb_input(screen, screen_dims[0] / 2 + 2,
                                                            screen_dims[1] / 2 - len(user_enabled_mask_prompt) / 2,
                                                            user_enabled_mask_prompt)
    show_console_in_status_window()
    configuration_dict["user_enabled_default"] = my_numb_input(screen, screen_dims[0]/2 + 4,
                                                               screen_dims[1]/2 - len(user_enabled_default_prompt)/2,
                                                               user_enabled_default_prompt)
    show_console_in_status_window()
    end_menu_call(screen, 13)


def menu_create_config(screen):
    screen_dims = setup_menu_call(screen, "14. Save/Create Configuration File")
    data = configuration_dict
    string_prompt = "Please specify a file name."
    path = my_raw_input(screen, screen_dims[0]/2, screen_dims[1]/2 - len(string_prompt)/2, string_prompt)
    return_values = configTool.save_config(data, path)
    if return_values["exit_status"] == 1:
        menu_options[13] = u"14. Save/Create Configuration File ✓"
        menu_color[13] = curses.color_pair(7)
    return_msg = return_values["message"]
    screen.addstr(screen_dims[0]/2 - 4, screen_dims[1]/2 - len(return_msg)/2, return_msg)
    end_msg = "Press m to go to the menu."
    screen.addstr(screen_dims[0]/2 - 3, screen_dims[1]/2 - len(end_msg)/2, end_msg)
    c = screen.getch()
    while c != (109):
        c = screen.getch()
    if c == 109:
        display_menu(screen, status_window)


def display_menu(screen, status_window):
    """Displays the menu. Does most of the work for displaying options."""
    screen_dimensions = screen.getmaxyx()
    screen_half_y = screen_dimensions[0]/2
    screen_half_x = screen_dimensions[1]/2
    screen.nodelay(0)
    screen.clear()
    screen.box()
    status_window.box()
    show_console_in_status_window()
    screen.refresh()

    menu_selection = -1
    option_num = 0
    while menu_selection < 0:
        menu_highlighting = [0] * 15 # number of menu options
        menu_highlighting[option_num] = curses.A_STANDOUT
        screen.addstr(screen_half_y - 9, screen_half_x - 11,
                      "LDAP Configuration Menu", curses.A_UNDERLINE | curses.color_pair(1) | curses.A_BOLD)
        screen.addstr(screen_half_y - 6, screen_half_x - 25,
                      menu_options[0].encode("utf-8"), menu_highlighting[0] | menu_color[0])
        screen.addstr(screen_half_y - 5, screen_half_x - 25,
                      menu_options[1].encode("utf-8"), menu_highlighting[1] | menu_color[1])
        screen.addstr(screen_half_y - 4, screen_half_x - 25,
                      menu_options[2].encode("utf-8"), menu_highlighting[2] | menu_color[2])
        screen.addstr(screen_half_y - 3, screen_half_x - 25,
                      menu_options[3].encode("utf-8"), menu_highlighting[3] | menu_color[3])
        screen.addstr(screen_half_y - 2, screen_half_x - 25,
                      menu_options[4].encode("utf-8"), menu_highlighting[4] | menu_color[4])
        screen.addstr(screen_half_y - 1, screen_half_x - 25,
                      menu_options[5].encode("utf-8"), menu_highlighting[5] | menu_color[5])
        screen.addstr(screen_half_y + 0, screen_half_x - 25,
                      menu_options[6].encode("utf-8"), menu_highlighting[6] | menu_color[6])
        screen.addstr(screen_half_y + 1, screen_half_x - 25,
                      menu_options[7].encode("utf-8"), menu_highlighting[7] | menu_color[7])
        screen.addstr(screen_half_y + 2, screen_half_x - 25,
                      menu_options[8].encode("utf-8"), menu_highlighting[8] | menu_color[8])
        screen.addstr(screen_half_y + 3, screen_half_x - 25,
                      menu_options[9].encode("utf-8"), menu_highlighting[9] | menu_color[9])
        screen.addstr(screen_half_y + 4, screen_half_x - 25,
                      menu_options[10].encode("utf-8"), menu_highlighting[10] | menu_color[10])
        screen.addstr(screen_half_y + 5, screen_half_x - 25,
                      menu_options[11].encode("utf-8"), menu_highlighting[11] | menu_color[11])
        screen.addstr(screen_half_y + 6, screen_half_x - 25,
                      menu_options[12].encode("utf-8"), menu_highlighting[12] | menu_color[12])
        screen.addstr(screen_half_y + 7, screen_half_x - 25,
                      menu_options[13].encode("utf-8"), menu_highlighting[13] | menu_color[13])
        screen.addstr(screen_half_y + 8, screen_half_x - 25, "15. Exit",
                      menu_highlighting[14] | curses.color_pair(3))
        screen.refresh()

        key_press = screen.getch()
        if key_press == curses.KEY_UP:
            option_num = (option_num - 1) % 15
        elif key_press == curses.KEY_DOWN:
            option_num = (option_num + 1) % 15
        elif key_press == ord('\n'):
            menu_selection = option_num
            if option_num == 0:
                menu_ping_ldap_ip(screen)
            elif option_num == 1:
                menu_check_ldap_connection_adv(screen)
            elif option_num == 2:
                menu_get_server_info(screen)
            elif option_num == 3:
                menu_check_ldap_suffix(screen)
            elif option_num == 4:
                menu_input_user_attributes(screen)
            elif option_num == 5:
                menu_show_list_user_object_classes(screen)
            elif option_num == 6:
                menu_check_user_tree_dn_show_users(screen)
            elif option_num == 7:
                menu_get_specific_user(screen)
            elif option_num == 8:
                menu_input_group_attributes(screen)
            elif option_num == 9:
                menu_show_list_group_object_classes(screen)
            elif option_num == 10:
                menu_check_group_tree_dn_show_groups(screen)
            elif option_num == 11:
                menu_get_specific_group(screen)
            elif option_num == 12:
                menu_additional_config_options(screen)
            elif option_num == 13:
                menu_create_config(screen)
            elif option_num == 14:
                if var_dict["conn_info"] != "none":
                    var_dict["conn_info"]["conn"].unbind()
                sys.exit(0)
            else:
                display_menu(screen, status_window)
    curses.curs_set(1)
curses.wrapper(show_instructions)
curses.endwin()