# -*- coding: utf-8 -*-
import curses
import locale
import os.path
import time
import sys
import yaml
import logging
from collections import OrderedDict

import klct.ldap.ldap_service as conn_service
from klct.log import logger
reload(sys)
sys.setdefaultencoding('utf8')
# sys.path.insert(0, '../ldap')
# import configTool
LOG = logging.getLogger(__name__)


timestamp_string = str(time.strftime('%B_%d_%Y_%X'))
"""SET UP"""
LOG.info("Setting up standard screen.")
locale.setlocale(locale.LC_ALL, "")  # for unicode support
stdscr = curses.initscr()  # terminal screen
stdscr_dimensions = stdscr.getmaxyx()
stdscr.keypad(True)
stdscr.scrollok(True)
curses.noecho()
LOG.info("Setting up Title screen.")
if curses.has_colors():  # enable coloring
    curses.start_color()
curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_WHITE)
curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(7, curses.COLOR_GREEN, curses.COLOR_WHITE)
curses.init_pair(8, curses.COLOR_BLUE, curses.COLOR_WHITE)
stdscr.bkgd(curses.color_pair(1))
LOG.info("Setting up status window.")
status_window = stdscr.subwin(stdscr_dimensions[0] - 2,
                              stdscr_dimensions[1] / 3 - 2, 1,
                              stdscr_dimensions[1] - stdscr_dimensions[1]/3)
status_window.scrollok(True)
status_window_text = stdscr.subwin(stdscr_dimensions[0] - 3,
                                   stdscr_dimensions[1] / 3 - 4, 2,
                                   stdscr_dimensions[1] - stdscr_dimensions[
                                       1]/3 + 1)
status_window_text.scrollok(True)
LOG.info("Setting up main screen")
main_window = stdscr.subwin(stdscr_dimensions[0] - 2,
                            stdscr_dimensions[1] - stdscr_dimensions[1] / 3 - 1
                            , 1, 1)
main_window.keypad(True)
main_window.scrollok(True)
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
configuration_dict = OrderedDict()

var_dict = {"conn_info": "none",
            "object_class": "none",
            "status_window": status_window,
            "status_window_text": status_window_text,
            "main_window": main_window,
            "port_added": False}

"""HELPER METHODS"""


def resize_windows():
    LOG.info("Resizing window")
    var_dict["status_window"].clear()
    var_dict["status_window_text"].clear()
    LOG.info("Status window cleared.")
    screen_dimensions = stdscr.getmaxyx()
    LOG.info("Getting new dimensions: " + str(screen_dimensions))
    var_dict["main_window"] = stdscr.subwin(
        screen_dimensions[0] - 2, screen_dimensions[1] -
        screen_dimensions[1] / 3 - 1, 1, 1)
    var_dict["main_window"].keypad(True)
    LOG.info("New main window created with dimensions: " +
             str(screen_dimensions[0] - 2)+"x" +
             str(screen_dimensions[1]-screen_dimensions[1] / 3 - 1) +
             " at coordinates: "+str(1)+", "+str(1))
    var_dict["status_window"] = stdscr.subwin(
        screen_dimensions[0] - 2,
        screen_dimensions[1] / 3 - 2, 1,
        screen_dimensions[1] - screen_dimensions[1] / 3)
    LOG.info("New status window created with dimensions: "+str(
        screen_dimensions[0] - 2)+"x"+str(screen_dimensions[1] / 3 - 2) +
             " at coordinates: "+str(1)+", "+str(screen_dimensions[1] -
                                                 screen_dimensions[1] / 3))
    var_dict["status_window_text"] = stdscr.subwin(
        screen_dimensions[0] - 4, screen_dimensions[1] / 3 - 4, 2,
        screen_dimensions[1] - screen_dimensions[1] / 3 + 1)
    LOG.info("New status window text created with dimensions: "+str(
        screen_dimensions[0] - 4)+"x"+str(screen_dimensions[1] / 3 - 4) +
             " at coordinates: "+str(2)+", "+str(screen_dimensions[1] -
                                                 screen_dimensions[1] / 3 + 1))

    show_console_in_status_window()
    stdscr.refresh()
    LOG.info("Standard Screen Refreshed")
    var_dict["main_window"].refresh()
    LOG.info("Main window Refreshed")
    status_window.refresh()
    LOG.info("Status window Refreshed")
    status_window_text.refresh()
    LOG.info("Status window Text Refreshed")


def display_list_with_numbers(screen, y, x, list_given):
    """Elements in list must be string."""
    num_elements = len(list_given)
    for i in range(num_elements):
        elem_i = str(list_given[i])
        elem_string = unicode("{i}. {elem}".format(i=i+1, elem=elem_i))
        screen.addstr(y + i, x, elem_string)


def display_list_with_numbers_test(screen, y, x, list_given):
    """Elements in list must be string."""
    num_elements = len(list_given)
    for i in range(num_elements):
        elem_i = str(list_given[i])
        elem_i = elem_i.replace('\n', "")
        # elem_temp = elem_i[index + 1]
        # elem_i[index] = ' '
        elem_string = unicode("{i}. {elem}".format(i=i+1, elem=elem_i))
        screen.addstr(y + i, x, elem_string)


def show_instructions(screen):
    """Displays the starting instructions prior to the menu display."""
    curses.curs_set(0)
    screen_dimensions = screen.getmaxyx()
    screen.clear()
    start_instruction = "HOS Keystone-LDAP Configuration Tool."
    screen.addstr(screen_dimensions[0]/2,
                  screen_dimensions[1]/2 - len(start_instruction)/2,
                  start_instruction, curses.A_BOLD | curses.A_COLOR)
    startup_commands = "Press 'm' to go to the menu or 'q' to quit."
    screen.addstr(screen_dimensions[0]/2 + 1, screen_dimensions[1]/2 - len(
        startup_commands)/2, startup_commands)
    screen.refresh()
    char_press = screen.getch()
    while char_press not in (109, 113):
        if char_press == curses.KEY_RESIZE:
            resize_windows()
            return show_instructions(stdscr)
        char_press = screen.getch()
    if char_press == 109:
        screen.clear()
        screen.refresh()
        display_menu()
    elif char_press == 113:
        sys.exit(0)


def my_raw_input_alt(screen, y, x, prompt_string):
    """Prompt for input from user. Given a (y, x) coordinate,
    will show a prompt at (y + 1, x). Currently only able to
    prompt for 20 chars, but can change later."""
    curses.echo()  # so user can see
    curses.curs_set(True)
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    str_input = screen.getstr(y + 1, x + 1, 255)
    curses.noecho()
    curses.curs_set(False)
    return str_input


def my_raw_input(screen, y, x, prompt_string, default=""):
    curses.noecho()
    curses.curs_set(True)
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    x_coord = x + 1
    str_input_pos = 0
    str_input = []
    c = screen.getch()
    while c != 10:  # 10 == '\n' newline character
        if c == curses.KEY_RESIZE:
            var_dict["status_window"].clear()
            var_dict["status_window_text"].clear()
            screen_dimensions = stdscr.getmaxyx()
            var_dict["main_window"] = stdscr.subwin(
                screen_dimensions[0] - 2, screen_dimensions[1] -
                screen_dimensions[1] / 4 - 1, 1, 1)
            var_dict["main_window"].keypad(True)
            var_dict["status_window"] = stdscr.subwin(
                screen_dimensions[0] - 2,
                screen_dimensions[1] / 4 - 2, 1,
                screen_dimensions[1] - screen_dimensions[1] / 4)
            var_dict["status_window_text"] = stdscr.subwin(
                screen_dimensions[0] - 4, screen_dimensions[1] / 4 - 4, 2,
                screen_dimensions[1] - screen_dimensions[1] / 4 + 1)

            show_console_in_status_window()
            stdscr.refresh()
            screen.refresh()
            status_window.refresh()
            status_window_text.refresh()
        elif c < 256:
            str_input.append(chr(c))
            screen.addch(y + 1, x_coord, str(chr(c)))
            x_coord += 1
            str_input_pos += 1
        elif c in (263, 8, 330):
            if x_coord > x + 1:
                x_coord -= 1
                screen.refresh()
            screen.addch(y + 1, x_coord, " ")
            if str_input_pos > 0:
                str_input_pos -= 1
            if len(str_input) > 0:
                str_input.pop()
        screen.move(y + 1, x_coord)
        c = screen.getch()
    string_input = ''.join(str_input)
    string_input = string_input.strip()
    if string_input == "":
        screen.addstr(y+1, x+1, str(default))
        return default
    curses.curs_set(False)
    curses.noecho()
    return string_input


def my_pw_input(screen, y, x, prompt_string):
    """Prompt for input from user. Given a (y, x) coordinate,
    will show a prompt at (y + 1, x). Will echo characters but as an '*',
    to hide the password's characters from showing on the screen."""
    curses.noecho()  # no echoing
    curses.curs_set(True)
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
        if c in (263, 8, 330):
            if x_coord > x + 1:
                x_coord -= 1
            screen.addch(y + 1, x_coord, " ")
            if str_input_pos > 0:
                str_input_pos -= 1
            if len(str_input) > 0:
                str_input.pop()
        screen.move(y + 1, x_coord)
        c = screen.getch()
    pw_input = ''.join(str_input)
    curses.curs_set(False)
    return pw_input


def prompt_char_input(screen, y, x, prompt_string, list_given):
    """Prompt for a single character input from user until user gives a char in
    list_given.Given a (y, x) coordinate, will show a prompt at (y + 1, x)."""
    curses.echo()  # no echoing
    curses.curs_set(True)
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    ch_input = screen.getstr(y + 1, x + 1, 1)  # 20 = max chars to in string
    while ch_input not in list_given:
        screen.addstr(y, x, "                                     ")
        screen.addstr(y + 1, x, "> ")
        screen.addstr(y, x, prompt_string, curses.color_pair(2))
        screen.refresh()
        ch_input = screen.getstr(y + 1, x + 1, 1)
    curses.noecho()
    curses.curs_set(False)
    return ch_input


def my_numb_input(screen, y, x, prompt_string, limit=None, default=None):
    curses.echo()
    curses.curs_set(True)
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addstr(y + 1, x, ">            ")
    screen.refresh()
    numb_input = screen.getstr(y + 1, x + 1, 10)
    numb_input = numb_input.strip()
    if numb_input == "":
        screen.addstr(y+1, x+1, str(default))
        curses.noecho()
        curses.curs_set(False)
        return default
    while not numb_input.isdigit():
        screen.addstr(y, x,
                      "                                                      ")
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
    Clears screen, adds title and returns max y and max x in tuple."""
    LOG.info("Setting up menu for: " + title)
    screen.clear()
    screen_dims = screen.getmaxyx()
    screen.addstr(screen_dims[0]/6, screen_dims[1]/2 - len(title)/2, title,
                  curses.color_pair(1) | curses.A_BOLD |
                  curses.A_UNDERLINE | curses.A_COLOR)
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
    screen.addstr(screen_dims[0]/6 + 2, screen_dims[1] / 2 - 28,
                  "Press 'n' for next step, 'r' to retry, or 'm' for menu.",
                  curses.A_BOLD | curses.color_pair(8) | curses.A_STANDOUT)
    character = screen.getch()
    while character not in (109, 110, 114):
        if character == curses.KEY_RESIZE:
            resize_windows()
        character = screen.getch()
    if character == 109:  # 109 == m
        display_menu()
    elif character == 110:  # 114 == r
        command_menu[current_step + 1]()
    elif character == 114:
        command_menu[current_step]()


def ip_not_exists(screen, screen_dims):
    screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 26,
                  "No valid IP found. Please complete the previous step",
                  curses.A_BOLD | curses.color_pair(3))
    screen.addstr(screen_dims[0] / 2 - 1, screen_dims[1] / 2 - 22,
                  "Press p to input ip address, or 'm' for menu",
                  curses.color_pair(5))
    key_press = screen.getch()
    while key_press not in (109, 112):  # 109 == m, 112 == p
        if key_press == curses.KEY_RESIZE:
            resize_windows()
        key_press = screen.getch()
    if key_press == 109:
        display_menu()
    elif key_press == 112:
        menu_ping_ldap_ip()


def adv_ldap_setup_prompts(screen, max_yx):
    host_ip = configuration_dict["url"]
    temp_str = my_numb_input(screen, max_yx[0] / 6 + 4, max_yx[1] / 2 - 22,
                             "Please enter the port number. Default is "
                             "389.", None, 389)

    port_numb = int(temp_str)

    userpw_y_or_n = prompt_char_input(screen, max_yx[0] / 6 + 6,
                                      max_yx[1] / 2 - 22,
                                      "Does LDAP server require User/Pass? "
                                      "[y/n]", ('y', 'n'))
    cert_prompt_offset = 14
    if userpw_y_or_n == 'y':
        user_name = my_raw_input(screen, max_yx[0] / 6 + 8, max_yx[1] / 2 - 22,
                                 "Please input your username.")
        # if want password hidden as "*" change my_raw_input to my_pw_input
        pass_wd = my_raw_input(screen, max_yx[0] / 6 + 10, max_yx[1] / 2 - 22,
                               "Please type your password.")
        tls_y_coord = max_yx[0] / 6 + 12
    else:
        cert_prompt_offset -= 4
        user_name = None
        pass_wd = None
        tls_y_coord = max_yx[0] / 6 + 8

    tls_y_or_n = prompt_char_input(screen, tls_y_coord, max_yx[1] / 2 - 22,
                                   "Is TLS enabled? Enter [y/n]", ('y', 'n'))
    if tls_y_or_n == 'n':
        tls_cert_path = None
    else:
        tls_cert_path = my_raw_input(screen,
                                     max_yx[0] / 6 + cert_prompt_offset,
                                     max_yx[1] / 2 - 22,
                                     "Please enter the path "
                                     "of the TLS certificate.")
        while not os.path.isfile(tls_cert_path):
            screen.addstr(max_yx[0] / 6 + cert_prompt_offset,
                          max_yx[1] / 2 - 22,
                          "                                              ")
            screen.addstr(max_yx[0] / 6 + cert_prompt_offset + 1,
                          max_yx[1] / 2 - 22,
                          ">                                              ")
            tls_cert_path = my_raw_input(screen,
                                         max_yx[0] / 6 + cert_prompt_offset,
                                         max_yx[1] / 2 - 22,
                                         "File not found. Please try again.")
    return [host_ip, port_numb, user_name, pass_wd, tls_y_or_n, tls_cert_path]


def adv_ldap_success(screen, conn_info, max_yx, user_name,
                     pass_word, port_numb, tls_cert_path=0):
    var_dict["conn_info"] = conn_info
    if var_dict["port_added"] == False:
        configuration_dict["url"] = configuration_dict["url"] + ":" + \
            str(port_numb)
        var_dict["port_added"] = True
    if user_name is not None:
        configuration_dict["user"] = user_name
    if pass_word is not None:
        configuration_dict["password"] = pass_word
    show_console_in_status_window()
    if tls_cert_path != 0:
        configuration_dict["tls_cacertfile"] = tls_cert_path
        show_console_in_status_window()
        screen.refresh()
    screen.addstr(max_yx[0] / 6 + 18,
                  max_yx[1] / 2 - len(conn_info['message']) / 2,
                  conn_info['message'],
                  curses.color_pair(6) | curses.A_BOLD)
    menu_options[1] = u"2. Check Connection to LDAP ✓"
    menu_color[1] = curses.color_pair(7)
    adv_ldap_end_prompt = "Press 'n' to move on to next step, 'r' to retry, " \
                          "or 'm' for " \
                          "menu."
    screen.addstr(max_yx[0] / 6 + 2, max_yx[1] / 2 -
                  len(adv_ldap_end_prompt) / 2,
                  adv_ldap_end_prompt,
                  curses.A_BOLD | curses.color_pair(8) | curses.A_STANDOUT)
    character = screen.getch()
    while character not in (109, 110, 114):
        if character == curses.KEY_RESIZE:
            resize_windows()
        character = screen.getch()
    if character == 109:  # 109 == m
        display_menu()
    elif character == 110:  # 110 == n
        menu_get_server_info()
    elif character == 114:
        menu_check_ldap_connection_adv(1)


def adv_ldap_fail(screen, conn_info, max_yx):
    menu_color[1] = curses.color_pair(3)
    screen.addstr(max_yx[0] / 6 + 18,
                  max_yx[1] / 2 - len(conn_info['message']) / 2,
                  conn_info['message'],
                  curses.color_pair(3) | curses.A_BOLD)

    screen.addstr(max_yx[0] / 6 + 2, max_yx[1] / 2 - 18,
                  "Press 'r' to retry, or 'm' for menu.", curses.color_pair(
            8) | curses.A_STANDOUT | curses.A_BOLD)
    char = screen.getch()
    while char not in (109, 114):
        if char == curses.KEY_RESIZE:
            resize_windows()
        char = screen.getch()
    if char == 109:
        display_menu()
    elif char == 114:
        menu_check_ldap_connection_adv(1)


def prompt_base_dn(screen):
    screen_dims = setup_menu_call(screen, "Prompt Base Distinguished Name")
    conn_info = var_dict["conn_info"]
    conn = conn_info['conn']
    prompt_str = "Please enter the base dn. (e.g. dc=openstack,dc=org)"
    base_dn = my_raw_input(screen, screen_dims[0] / 6 + 6,
                           screen_dims[1] / 2 - len(prompt_str) / 2,
                           prompt_str)
    screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 10,
                  "Validating suffix (base DN)...",
                  curses.color_pair(5) | curses.A_BOLD)
    screen.refresh()
    results = conn_service.check_ldap_suffix(conn, base_dn)
    screen.addstr(screen_dims[0] / 2 - 2, screen_dims[1] / 2 - 10,
                  "                              ")
    if results["exit_status"] == 1:
        configuration_dict["suffix"] = base_dn
        menu_options[3] = u"4. Check LDAP Suffix ✓"
        menu_color[3] = curses.color_pair(7)
        show_console_in_status_window()
        end_message = "{base} is valid and has been added to " \
                      "configuration.".format(
                        base=base_dn)
        screen.addstr(screen_dims[0] / 2 - 4,
                      screen_dims[1] / 2 - len(
                      end_message) / 2,
                      end_message,
                      curses.color_pair(6) |
                      curses.A_BOLD)
        screen.addstr(screen_dims[0] / 6 + 2, screen_dims[1] / 2 - 25,
                      "Press 'n' for next step, 'r' to retry, or 'm' for "
                      "menu.",
                      curses.A_BOLD | curses.A_STANDOUT | curses.color_pair(8))
    else:
        message_color = 3
        screen.addstr(screen_dims[0] / 6 + 2,
                      screen_dims[1] / 2 - len(results['message']) / 2,
                      results['message'],
                      curses.color_pair(message_color) | curses.A_BOLD)
        screen.addstr(screen_dims[0] / 6 + 2, screen_dims[1] / 2 - 28,
                      "Press 'n' for next step, 'r' to retry, or 'm' for "
                      "menu.",
                      curses.A_BOLD | curses.A_STANDOUT | curses.color_pair(8))
    c = screen.getch()
    while c not in (109, 110, 114):
        if c == curses.KEY_RESIZE:
            resize_windows()
        c = screen.getch()
    if c == 109:
        display_menu()
    elif c == 110:
        menu_input_user_attributes()
    elif c == 114:
        menu_check_ldap_suffix()


"""MENU METHODS"""


def show_console_in_status_window():
    LOG.info("Updating console window.")
    var_dict["status_window"].clear()
    var_dict["status_window_text"].clear()
    var_dict["status_window"].box()
    var_dict["status_window_text"].addstr(0, 0, "Keystone-LDAP Configuration",
                                          curses.A_BOLD | curses.A_UNDERLINE)
    if bool(configuration_dict):
        global timestamp_string
        tmpfile = "temp_conf_" + timestamp_string + ".yaml"
        conn_service.save_config(configuration_dict, tmpfile)
        configuration_dict_yaml_str = \
            conn_service.save_config(configuration_dict, None)
        # configuration_dict_yaml_str = yaml.dump(configuration_dict,
        #                                         stream=None,
        #                                         default_flow_style=False)
        var_dict["status_window_text"].addstr(1, 0,
                                              configuration_dict_yaml_str)
    var_dict["status_window"].refresh()
    var_dict["status_window_text"].refresh()


def menu_ping_ldap_ip():
    """Displays a screen prompting user for IP address and then
    pings that IP address to see if it able to send a response."""
    LOG.info("Prompting for IP.")
    screen_dims = setup_menu_call(var_dict["main_window"],
                                  "1. Enter/Validate LDAP Server IP")
    prompt_ip_string = "Please Enter the IP Address of the LDAP server."
    ip_string = my_raw_input(var_dict["main_window"], screen_dims[0] / 6 + 4,
                             screen_dims[1] / 2 - len(prompt_ip_string)/2,
                             prompt_ip_string)
    var_dict["main_window"].addstr(screen_dims[0] / 2 - 7,
                                   screen_dims[1] / 2 - 12,
                                   "Attempting to ping IP...",
                                   curses.color_pair(5) | curses.A_BLINK)
    var_dict["main_window"].refresh()

    results = conn_service.ping_ldap_server(ip_string)
    var_dict["main_window"].addstr(screen_dims[0] / 2 - 7,
                                   screen_dims[1] / 2 - 12,
                                   "                        ")
    if results['exit_status'] == 1 and ip_string != "":
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 7,
                                       screen_dims[1] / 2 -
                                       len(results['message']) / 2,
                                       results['message'],
                                       curses.color_pair(6) | curses.A_BOLD)
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 8,
                                       screen_dims[1] / 2 - 26,
                                       "This IP will automatically be used in "
                                       "the next steps.",
                                       curses.color_pair(4) | curses.A_BOLD)
        end_msg = "Press 'n' to move on to next step, 'r' to retry, or 'm' " \
                  "for menu."
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 2,
                                       screen_dims[1] / 2 - len(end_msg) / 2,
                                       end_msg, curses.A_BOLD |
                                       curses.color_pair(8) |
                                       curses.A_STANDOUT)
        menu_options[0] = u"1. Ping LDAP Server IP ✓"
        menu_color[0] = curses.color_pair(7)
        configuration_dict["url"] = results['host_name']
        show_console_in_status_window()
    else:
        if "url" not in configuration_dict:
            menu_color[0] = curses.color_pair(3)
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 7,
                                       screen_dims[1] / 2 -
                                       len(results['message']) / 2,
                                       results['message'],
                                       curses.color_pair(3))
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 2,
                                       screen_dims[1] / 2 - 23,
                                       "Press 'r' to retry this step, "
                                       "or 'm' for menu.",
                                       curses.A_BOLD | curses.A_STANDOUT |
                                       curses.color_pair(8))
    temp_char = var_dict["main_window"].getch()
    while temp_char not in (110, 109, 114):  # 109 = 'm', 110 = 'n', 114 = 'r'
        if temp_char == curses.KEY_RESIZE:
            resize_windows()
        temp_char = var_dict["main_window"].getch()
    if temp_char == 109:
        display_menu()
    elif temp_char == 110:
        menu_check_ldap_connection_adv(1)
    elif temp_char == 114:
        menu_ping_ldap_ip()


def menu_check_ldap_connection_adv(skip=0):
    max_yx = setup_menu_call(var_dict["main_window"],
                             "2. Check Connection to LDAP Server")
    if "url" not in configuration_dict:
        LOG.debug("No ip found.")
        ip_not_exists(var_dict["main_window"], max_yx)
    else:
        if skip == 0:
            y_n = prompt_char_input(
                var_dict["main_window"], max_yx[0] / 2 - 4, max_yx[1] / 2 - 26,
                "Valid IP has been found, would you like to use this? [y/n]",
                ('y', 'n'))
        else:
            y_n = 'y'
        setup_menu_call(var_dict["main_window"],
                        "2. Check Connection to LDAP Server")
        if y_n == 'y':
            LOG.info("Prompting for connection information.")
            adv_ldap_inputs = adv_ldap_setup_prompts(var_dict["main_window"],
                                                     max_yx)
            host_ip = adv_ldap_inputs[0]
            port_numb = adv_ldap_inputs[1]
            user_name = adv_ldap_inputs[2]
            pass_wd = adv_ldap_inputs[3]
            tls_y_or_n = adv_ldap_inputs[4]
            tls_cert_path = adv_ldap_inputs[5]
            attempt_message = "Attempting to connect to LDAP server... This " \
                "may take a while."
            var_dict["main_window"].addstr(
                max_yx[0] / 6 + 17, max_yx[1] / 2 - len(attempt_message)/2,
                attempt_message,
                curses.color_pair(5))
            var_dict["main_window"].refresh()
            conn_info = conn_service.connect_ldap_server(host_ip, port_numb,
                                                         user_name, pass_wd,
                                                         tls_y_or_n,
                                                         tls_cert_path)
            var_dict["main_window"].addstr(
                max_yx[0] / 6 + 17,
                max_yx[1] / 2 - len(attempt_message)/2,
                "                                                             "
                "   ")
            if conn_info['exit_status'] == 1:
                if tls_cert_path is not None:
                    adv_ldap_success(var_dict["main_window"],
                                     conn_info, max_yx, user_name, pass_wd,
                                     port_numb, tls_cert_path)
                else:
                    adv_ldap_success(var_dict["main_window"],
                                     conn_info, max_yx, user_name, pass_wd,
                                     port_numb)
            else:  # error occurred during ldap ping
                adv_ldap_fail(var_dict["main_window"], conn_info, max_yx)
        else:
            menu_ping_ldap_ip()


def menu_get_server_info():
    """Displays server information on screen.
    Currently only displays version and type,  but later will add
    more information."""
    screen_dims = setup_menu_call(var_dict["main_window"],
                                  "3. Get Server Information")
    if var_dict["conn_info"] == "none":
        error_msg = "No LDAP server found. Press any key to go to the menu."
        var_dict["main_window"].addstr(screen_dims[0] / 2,
                                       screen_dims[1] / 2 - len(error_msg)/2,
                                       error_msg,
                                       curses.color_pair(3) | curses.A_BOLD)
        var_dict["main_window"].getch()
        display_menu()
    else:
        conn_info = var_dict["conn_info"]
        server = conn_info["server"]
        server_info_dict = conn_service.retrieve_server_info(conn_info["conn"],
                                                             server)
        if server_info_dict["exit_status"] == 1:
            menu_options[2] = u"3. Get Server Information ✓"
            menu_color[2] = curses.color_pair(7)
            version = str(server_info_dict["version"])
            ldap_type = str(server_info_dict["type"])
            strlen = len(ldap_type)
            if len(version) > len(ldap_type):
                strlen = len(version)
            var_dict["main_window"].addstr(screen_dims[0] / 6 + 6,
                                           screen_dims[1] / 2 - strlen/2,
                                           version, curses.color_pair(5))
            var_dict["main_window"].addstr(screen_dims[0] / 6 + 7,
                                           screen_dims[1] / 2 - strlen/2,
                                           ldap_type, curses.color_pair(5))
            var_dict["main_window"].refresh()
        else:
            menu_color[2] = curses.color_pair(3)
            var_dict["main_window"].addstr(screen_dims[0]/2 + 1,
                                           screen_dims[1]/2, "Error",
                                           curses.color_pair(3))

        var_dict["main_window"].addstr(screen_dims[0] / 6 + 4,
                                       screen_dims[1] / 2 - 10,
                                       "Server Information:", curses.A_BOLD)
        end_menu_call(var_dict["main_window"], 3)


def menu_check_ldap_suffix():
    """If failure, may be due to invalid credentials.
    May want to alert user of this later on."""
    screen_dims = setup_menu_call(var_dict["main_window"],
                                  "4. Check LDAP Suffix")
    if var_dict["conn_info"] == "none":
        var_dict["main_window"].addstr(screen_dims[0] / 2,
                                       screen_dims[1] / 2 - 28,
                                       "No LDAP server found. "
                                       "Press any key to go to menu.")
        var_dict["main_window"].getch()
        display_menu()
    else:
        var_dict["main_window"].addstr(screen_dims[0] / 2,
                                       screen_dims[1] / 2 - 9,
                                       "Fetching base dn...",
                                       curses.color_pair(5))
        server = var_dict["conn_info"]["server"]
        ret_vals = conn_service.get_ldap_suffix(server)
        var_dict["main_window"].addstr(screen_dims[0] / 2,
                                       screen_dims[1] / 2 - 9,
                                       "                   ")
        if ret_vals["exit_status"] == 0:
            menu_color[3] = curses.color_pair(3)
            var_dict["main_window"].addstr(screen_dims[0] / 2 + 1,
                                           screen_dims[1] / 2 - 23,
                                           "Unable to find base dn. "
                                           "Please input a base dn")
            prompt_base_dn(var_dict["main_window"])
        elif ret_vals["exit_status"] == 1:
            base_dn = ret_vals['base_dn']
            menu_options[3] = u"4. Check LDAP Suffix ✓"
            menu_color[3] = curses.color_pair(7)
            var_dict["main_window"].addstr(screen_dims[0] / 6 + 6,
                                           screen_dims[1] / 2 -
                                           (len(base_dn)/2 + 8),
                                           base_dn + " is your base dn.",
                                           curses.A_BOLD)
            y_n = prompt_char_input(var_dict["main_window"],
                                    screen_dims[0] / 6 + 7,
                                    screen_dims[1] / 2 - 18,
                                    "Is this information correct? [y/n]",
                                    ('y', 'n'))
            if y_n == 'n':
                return prompt_base_dn(var_dict["main_window"])
            else:
                configuration_dict["suffix"] = base_dn
                show_console_in_status_window()
                end_message = "{base} added to configuration file.".format(
                    base=base_dn)
                var_dict["main_window"].addstr(screen_dims[0] / 2 - 4,
                                               screen_dims[1] / 2 - len(
                                               end_message) / 2,
                                               end_message,
                                               curses.color_pair(6) |
                                               curses.A_BOLD)

        end_menu_call(var_dict["main_window"], 4)


def menu_input_user_attributes():
    screen_dims = setup_menu_call(
        var_dict["main_window"],
        "5. Input User ID Attribute/User Name Attribute")
    if var_dict["conn_info"] == "none":
        var_dict["main_window"].addstr(screen_dims[0] / 2,
                                       screen_dims[1] / 2 - 23,
                                       "No LDAP server found. "
                                       "Press any key to go to the menu.")
        var_dict["main_window"].getch()
        display_menu()
    else:
        LOG.info("Prompting for user information.")
        user_id_attr_prompt = "What is the user id attribute?"
        user_name_attr_prompt = "What is the user name attribute?"
        user_tree_dn_prompt = "What is the user tree DN, " \
                              "not including the base DN (e.g. ou=Users)?"
        if "suffix" in configuration_dict:
            user_tree_dn = my_raw_input(var_dict["main_window"],
                                        screen_dims[0] / 6 + 4, screen_dims[
                                            1] /
                                        2 - len(user_tree_dn_prompt) / 2,
                                        user_tree_dn_prompt)
            user_id_attribute = my_raw_input(
                var_dict["main_window"],
                screen_dims[0] / 6 + 6,
                screen_dims[1] / 2 - len(user_tree_dn_prompt) / 2,
                user_id_attr_prompt)
            user_name_attribute = my_raw_input(
                var_dict["main_window"],
                screen_dims[0] / 6 + 8,
                screen_dims[1] / 2 - len(user_tree_dn_prompt) / 2,
                user_name_attr_prompt)
        else:
            var_dict["main_window"].addstr(
                screen_dims[0] / 2, screen_dims[1] / 2 - 29,
                "No Suffix (base DN) found. Press any key to go to the menu.")
            var_dict["main_window"].getch()
            return display_menu()
        attempt_message = "Verifying information... Please wait."
        blank_message = "                                     "
        var_dict["main_window"].addstr(
            screen_dims[0] / 6 + 17,
            screen_dims[1] / 2 - len(attempt_message) / 2,
            attempt_message,
            curses.color_pair(5))
        var_dict["main_window"].refresh()
        results = conn_service.validate_info(
            var_dict["conn_info"]["conn"],
            user_tree_dn + "," + configuration_dict["suffix"],
            user_id_attribute, user_name_attribute)
        var_dict["main_window"].addstr(
            screen_dims[0] / 6 + 17,
            screen_dims[1] / 2 - len(attempt_message) / 2,
            blank_message)
        var_dict["main_window"].refresh()
        if results["exit_status"] == 1:
            configuration_dict["user_tree_dn"] = user_tree_dn +\
                                                 "," +\
                                                 configuration_dict["suffix"]
            configuration_dict["user_id_attribute"] = user_id_attribute
            configuration_dict["user_name_attribute"] = user_name_attribute
            show_console_in_status_window()
            menu_options[4] = u"5. Input User ID Attribute/" \
                              u"User Name Attribute ✓"
            menu_color[4] = curses.color_pair(7)
            var_dict["main_window"].addstr(
                screen_dims[0] / 6 + 11,
                screen_dims[1] / 2 - len(results['message']) / 2,
                results['message'], curses.color_pair(6) | curses.A_BOLD)
            update_message = "Configuration has been updated with this " \
                             "information."
            var_dict["main_window"].addstr(
                screen_dims[0] / 6 + 12,
                screen_dims[1] / 2 - len(update_message) / 2,
                update_message, curses.color_pair(6) | curses.A_BOLD)
        else:
            var_dict["main_window"].addstr(
                screen_dims[0] / 6 + 11,
                screen_dims[1] / 2 - len(results['message']) / 2,
                results['message'], curses.color_pair(3) | curses.A_BOLD)
            error_message = "The information entered is incorrect. Please " \
                            "retry this step."
            var_dict["main_window"].addstr(
                screen_dims[0] / 6 + 12,
                screen_dims[1] / 2 - len(error_message) / 2,
                error_message, curses.color_pair(3) | curses.A_BOLD)
            menu_color[4] = curses.color_pair(3)
        end_menu_call(var_dict["main_window"], 5)


def menu_show_list_user_object_classes():
    screen_dims = setup_menu_call(
        var_dict["main_window"],
        "6. Show List of User-Related ObjectClasses")
    var_dict["main_window"].refresh()
    if var_dict["conn_info"] == "none" or "suffix" not in configuration_dict:
        prompt_string = "No connection to server found or no " \
                        "suffix (base DN). Press 'm' to go to menu."
        var_dict["main_window"].addstr(screen_dims[0] / 2, screen_dims[1] / 2 -
                                       len(prompt_string)/2, prompt_string,
                                       curses.color_pair(3) | curses.A_BOLD)
        var_dict["main_window"].getch()
        display_menu()
    else:
        retrieving_string = "Retrieving list of object classes..."
        blnk_retrieve_str = "                                    "
        var_dict["main_window"].addstr(screen_dims[0]/2 - 2, screen_dims[1]/2 -
                                       len(retrieving_string)/2,
                                       retrieving_string,
                                       curses.color_pair(5))
        var_dict["main_window"].refresh()
        conn_info = var_dict["conn_info"]
        conn = conn_info['conn']
        # base_dn = configuration_dict["suffix"]
        if "user_id_attribute" in configuration_dict and "user_tree_dn" in \
                configuration_dict:
            user_id_attribute = configuration_dict["user_id_attribute"]
            user_dn = configuration_dict["user_tree_dn"]
            return_values = conn_service.list_object_classes(
                conn, user_dn, user_id_attribute)
            var_dict["main_window"].addstr(
                screen_dims[0] / 2 - 2,
                screen_dims[1] / 2 - len(blnk_retrieve_str) / 2,
                blnk_retrieve_str)
            if return_values['exit_status'] == 1:
                LOG.info("Displaying user object classes.")
                menu_options[5] = \
                    u"6. Show List of User-Related ObjectClasses ✓"
                menu_color[5] = curses.color_pair(7)
                var_dict["main_window"].addstr(screen_dims[0] / 6 + 4,
                                               screen_dims[1] / 2 - 15,
                                               "User Object classes:")
                object_classes_list = return_values['objectclasses'] +\
                    ["None of the above"]
                display_list_with_numbers(
                    var_dict["main_window"],
                    screen_dims[0]/6 + 5, screen_dims[1]/2 - 15,
                    object_classes_list)
                num_obj_classes = len(object_classes_list)
                choice = my_numb_input(
                    var_dict["main_window"],
                    screen_dims[0]/6 + num_obj_classes + 5,
                    screen_dims[1]/2 - 15,
                    "Please choose a number.", num_obj_classes)
                if choice == num_obj_classes:
                    usr_obj_class = my_raw_input(
                        var_dict["main_window"],
                        screen_dims[0]/6 + num_obj_classes + 7,
                        screen_dims[1]/2 - 15,
                        "Please enter the user object class")
                    ret = conn_service.validate_object_class(conn, user_dn,
                                                             usr_obj_class)
                    color = 3
                    if ret['exit_status'] == 1:
                        configuration_dict["user_object_class"] = usr_obj_class
                        color = 6
                    var_dict["main_window"].addstr(
                        screen_dims[0] / 2 - 3,
                        screen_dims[1] / 2 - 12, ret['message'],
                        curses.color_pair(color) | curses.A_BOLD)
                    end_menu_call(var_dict["main_window"], 6)
                else:
                    usr_obj_class = str(object_classes_list[choice - 1])
                configuration_dict["user_object_class"] = usr_obj_class
                end_message = "{usr_ojbc} has been added to " \
                              "configuration.".format(usr_ojbc=usr_obj_class)
                var_dict["main_window"].addstr(screen_dims[0]/2 - 4,
                                               screen_dims[1]/2 - len(
                                                   end_message)/2,
                                               end_message,
                                               curses.color_pair(6) |
                                               curses.A_BOLD)
                show_console_in_status_window()
                return end_menu_call(var_dict["main_window"], 6)
            else:
                menu_color[5] = curses.color_pair(3)
                var_dict["main_window"].addstr(
                    screen_dims[0] / 2 - 3,
                    screen_dims[1] / 2 - 12, "No object classes found.")
                return end_menu_call(var_dict["main_window"], 6)
        else:
            var_dict["main_window"].addstr(
                screen_dims[0] / 2 - 2,
                screen_dims[1] / 2 - len(blnk_retrieve_str) / 2,
                blnk_retrieve_str)
            error_prompt = "Please input the user id attribute in step 5."
            var_dict["main_window"].addstr(
                screen_dims[0] / 2 - 4,
                screen_dims[1] / 2 - len(error_prompt) / 2, error_prompt,
                curses.color_pair(3) | curses.A_BOLD)
            var_dict["main_window"].addstr(
                screen_dims[0] / 6 + 2,
                screen_dims[1] / 2 - 14, "Press 'm' to go to the menu.",
                curses.A_BOLD | curses.A_STANDOUT | curses.color_pair(8))
            c = var_dict["main_window"].getch()
            while c != 109:
                c = var_dict["main_window"].getch()
            if c == 109:
                display_menu()


def check_user_config_dict(screen_dims):
    if var_dict["conn_info"] == "none":
        no_conn_info_msg = \
            "No LDAP server found. Please complete steps 1 and 2."
        var_dict["main_window"].addstr(
            screen_dims[0]/2,
            screen_dims[1]/2 - len(no_conn_info_msg)/2, no_conn_info_msg,
            curses.color_pair(3) | curses.A_BOLD)
        if "user_tree_dn" not in configuration_dict \
                or "user_id_attribute" not in configuration_dict \
                or "user_object_class" not in configuration_dict:
            no_user_info_msg = \
                "Could not find user attribute information. " \
                "Please complete step 5."
            var_dict["main_window"].addstr(
                screen_dims[0] / 2 + 2,
                screen_dims[1] / 2 - len(no_user_info_msg)/2, no_user_info_msg,
                curses.color_pair(3) | curses.A_BOLD)
        return False
    if "user_tree_dn" not in configuration_dict \
            or "user_id_attribute" not in configuration_dict \
            or "user_object_class" not in configuration_dict:
        no_user_info_msg = \
            "Could not find user attribute information. " \
            "Please complete step 5."
        var_dict["main_window"].addstr(
            screen_dims[0]/2 + 2,
            screen_dims[1]/2 - len(no_user_info_msg), no_user_info_msg,
            curses.color_pair(3) | curses.A_BOLD)
        return False
    return True


def menu_check_user_tree_dn_show_users():
    screen_dims = setup_menu_call(
        var_dict["main_window"],
        "7. Check User Tree DN and Show List of Users")
    if check_user_config_dict(screen_dims):
        conn = var_dict["conn_info"]["conn"]
        user_tree_dn = configuration_dict["user_tree_dn"]
        user_id_attribute = configuration_dict["user_id_attribute"]
        object_class = configuration_dict["user_object_class"]
        maximum = screen_dims[0] - screen_dims[0]/6 - 7
        limit_prompt = "How many users would you like to see? Maximum: {" \
                       "max}".format(max=maximum)
        limit = my_numb_input(var_dict["main_window"], screen_dims[0]/6 + 4,
                              screen_dims[1]/8, limit_prompt)
        limit = min(maximum, limit)
        return_values = conn_service.list_entries(conn, user_tree_dn,
                                                  user_id_attribute,
                                                  object_class, limit)
    else:
        return_values = {"exit_status": 0}
    if return_values["exit_status"] == 1:
        LOG.info("Listing Users.")
        menu_options[6] = u"7. Check User Tree DN and Show List of Users ✓"
        menu_color[6] = curses.color_pair(7)
        list_of_users = return_values["entries"]
        var_dict["list_of_users"] = list_of_users
        var_dict["main_window"].addstr(screen_dims[0]/6 + 6, 0, "List of "
                                                                "Users",
                                       curses.A_BOLD | curses.A_UNDERLINE |
                                       curses.color_pair(8))
        display_list_with_numbers_test(var_dict["main_window"],
                                       screen_dims[0]/6 + 7,
                                       0, list_of_users)
        var_dict["main_window"].refresh()
        end_menu_call(var_dict["main_window"], 7)
    else:
        menu_color[6] = curses.color_pair(3)
        err_msg = "Unable to retrieve users"
        var_dict["main_window"].addstr(screen_dims[0]/2 - 2,
                                       screen_dims[1]/2 - len(err_msg)/2,
                                       err_msg,
                                       curses.color_pair(3) | curses.A_BOLD)
        end_menu_call(var_dict["main_window"], 7)


def menu_get_specific_user():
    screen_dims = setup_menu_call(var_dict["main_window"],
                                  "8. Get a Specific User")
    if check_user_config_dict(screen_dims):
        if "list_of_users" not in var_dict:
            return menu_check_user_tree_dn_show_users()
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 6, 0, "List of "
                                                                  "Users",
                                       curses.A_BOLD | curses.A_UNDERLINE |
                                       curses.color_pair(8))
        display_list_with_numbers_test(var_dict["main_window"],
                                       screen_dims[0] / 6 + 7,
                                       0, var_dict["list_of_users"])
        var_dict["main_window"].refresh()
        conn = var_dict["conn_info"]["conn"]
        user_dn = configuration_dict["user_tree_dn"]
        user_id_attribute = configuration_dict["user_id_attribute"]
        object_class = configuration_dict["user_object_class"]
        user_name_attribute = configuration_dict["user_name_attribute"]
        name_msg_prompt = "What is the user name you would like to get?"
        name = my_raw_input(var_dict["main_window"], screen_dims[0]/6 + 3,
                            screen_dims[1]/2 - len(name_msg_prompt),
                            name_msg_prompt)
        return_values = conn_service.get_entry(conn, user_dn,
                                               user_id_attribute,
                                               object_class,
                                               user_name_attribute,
                                               name)
        screen_dims = setup_menu_call(var_dict["main_window"],
                                      "8. Get a Specific User")
    else:
        return_values = {"exit_status": 0}
    if return_values["exit_status"] == 1:
        LOG.info("Successfully retrieved specific user.")
        menu_options[7] = u"8. Get a Specific User ✓"
        menu_color[7] = curses.color_pair(7)
        user = return_values["entry"]
        var_dict["main_window"].addstr(screen_dims[0]/6 + 5, 0, "User: "
                                       "{usr}".format(usr=name),
                                       curses.A_UNDERLINE | curses.A_BOLD |
                                       curses.color_pair(8))
        display_list_with_numbers(var_dict["main_window"], screen_dims[0] /
                                  6 + 6,
                                  0, user)
        end_menu_call(var_dict["main_window"], 8)
    else:
        menu_color[7] = curses.color_pair(3)
        err_msg = "Unable to retrieve user"
        var_dict["main_window"].addstr(screen_dims[0]/2 - 2, screen_dims[1]/2 -
                                       len(err_msg)/2, err_msg,
                                       curses.color_pair(3) | curses.A_BOLD)
        end_menu_call(var_dict["main_window"], 8)


def menu_input_group_attributes():
    screen_dims = setup_menu_call(
        var_dict["main_window"],
        "9. Input Group ID Attribute/Group Name Attribute")
    if var_dict["conn_info"] == "none":
        var_dict["main_window"].addstr(screen_dims[0] / 2,
                                       screen_dims[1] / 2 - 23,
                                       "No LDAP server found. "
                                       "Press any key to go to the menu.")
        var_dict["main_window"].getch()
        display_menu()
    else:
        LOG.info("Prompting for group info.")
        group_id_attr_prompt = "What is the group id attribute?"
        group_name_attr_prompt = "What is the group name attribute?"
        group_tree_dn_prompt = \
            "What is the group tree DN, " \
            "not including the base DN (e.g. ou=Groups)?"

        if "suffix" in configuration_dict:
            group_tree_dn = my_raw_input(
                var_dict["main_window"],
                screen_dims[0] / 6 + 4,
                screen_dims[1] / 2 - len(group_tree_dn_prompt) / 2,
                group_tree_dn_prompt)
            group_id_attribute = my_raw_input(
                var_dict["main_window"],
                screen_dims[0] / 6 + 6,
                screen_dims[1] / 2 - len(group_tree_dn_prompt) / 2,
                group_id_attr_prompt)
            group_name_attribute = my_raw_input(
                var_dict["main_window"],
                screen_dims[0] / 6 + 8,
                screen_dims[1] / 2 - len(group_tree_dn_prompt) / 2,
                group_name_attr_prompt)
        else:
            var_dict["main_window"].addstr(
                screen_dims[0] / 2, screen_dims[1] / 2 - 29,
                "No Suffix (base DN) found. Press any key to go to the menu.")
            var_dict["main_window"].getch()
            display_menu()
        attempt_message = "Verifying information... Please wait."
        blank_message = "                                     "
        var_dict["main_window"].addstr(
            screen_dims[0] / 6 + 17,
            screen_dims[1] / 2 - len(attempt_message) / 2,
            attempt_message,
            curses.color_pair(5))
        var_dict["main_window"].refresh()
        results = conn_service.validate_info(var_dict["conn_info"]["conn"],
                                             group_tree_dn + "," +
                                             configuration_dict["suffix"],
                                             group_id_attribute,
                                             group_name_attribute)
        var_dict["main_window"].addstr(
            screen_dims[0] / 6 + 17,
            screen_dims[1] / 2 - len(attempt_message) / 2,
            blank_message)
        var_dict["main_window"].refresh()
        if results["exit_status"] == 1:
            configuration_dict["group_id_attribute"] = group_id_attribute
            configuration_dict["group_name_attribute"] = group_name_attribute
            configuration_dict["group_tree_dn"] = \
                group_tree_dn + "," + configuration_dict["suffix"]
            show_console_in_status_window()
            menu_options[8] = \
                u"9. Input Group ID Attribute/Group Name Attribute ✓"
            menu_color[8] = curses.color_pair(7)
        else:
            var_dict["main_window"].addstr(
                screen_dims[0] / 6 + 11,
                screen_dims[1] / 2 - len(results['message']) / 2,
                results['message'], curses.color_pair(3) | curses.A_BOLD)
            error_message = "The information entered is incorrect. Please " \
                            "retry this step."
            var_dict["main_window"].addstr(
                screen_dims[0] / 6 + 12,
                screen_dims[1] / 2 - len(error_message) / 2,
                error_message, curses.color_pair(3) | curses.A_BOLD)
            menu_color[8] = curses.color_pair(3)
        var_dict["main_window"].addstr(
            screen_dims[0] / 6 + 11,
            screen_dims[1] / 2 - len(results['message']) / 2,
            results['message'], curses.color_pair(6) | curses.A_BOLD)
        update_message = "Configuration has been updated with this " \
                         "information."
        var_dict["main_window"].addstr(
            screen_dims[0] / 6 + 12,
            screen_dims[1] / 2 - len(update_message) / 2,
            update_message, curses.color_pair(6) | curses.A_BOLD)
    end_menu_call(var_dict["main_window"], 9)


def check_group_config_dict(screen_dims):
    if var_dict["conn_info"] == "none":
        no_conn_info_msg =\
            "No LDAP server found. Please complete steps 1 and 2."
        var_dict["main_window"].addstr(
            screen_dims[0]/2, screen_dims[1]/2 - len(no_conn_info_msg)/2,
            no_conn_info_msg, curses.color_pair(3) | curses.A_BOLD)
        return False
    if "group_tree_dn" not in configuration_dict or \
            "group_id_attribute" not in configuration_dict or \
            "group_name_attribute" not in configuration_dict:
        no_group_info_msg = "Could not find group attribute information" \
                            ". Please complete step 9."
        var_dict["main_window"].addstr(screen_dims[0]/2 + 2, screen_dims[
            1]/2 - len(no_group_info_msg), no_group_info_msg,
                      curses.color_pair(3) | curses.A_BOLD)
        return False
    return True


def menu_show_list_group_object_classes():
    screen_dims = setup_menu_call(
        var_dict["main_window"],
        "10. Show List of Group Related ObjectClasses")
    if check_group_config_dict(screen_dims):
        conn = var_dict["conn_info"]["conn"]
        group_dn = configuration_dict["group_tree_dn"]
        group_id_attribute = configuration_dict["group_id_attribute"]
        return_values = conn_service.list_object_classes(conn, group_dn,
                                                         group_id_attribute)
    else:
        return_values = {"exit_status": 0}
    if return_values["exit_status"] == 1:
        LOG.info("Displaying group object classes.")
        object_classes_list = return_values['objectclasses'] + \
            ["None of the above"]
        display_list_with_numbers(var_dict["main_window"],
                                  screen_dims[0] / 6 + 5,
                                  screen_dims[1] / 2 - 15,
                                  object_classes_list)
        num_obj_classes = len(object_classes_list)
        choice = my_numb_input(
            var_dict["main_window"],
            screen_dims[0] / 6 + num_obj_classes + 5, screen_dims[1] / 2 - 15,
            "Please choose one of the above.", num_obj_classes)
        if choice == num_obj_classes:
            group_obj_class = my_raw_input(
                var_dict["main_window"],
                screen_dims[0] / 6 + num_obj_classes + 7,
                screen_dims[1] / 2 - 15,
                "Please enter the group object class")
            ret = conn_service.validate_object_class(conn, group_dn,
                                                     group_obj_class)
            color = 3
            if ret['exit_status'] == 1:
                configuration_dict["group_object_class"] = group_obj_class
                color = 6
            var_dict["main_window"].addstr(
                screen_dims[0] / 2 - 3,
                screen_dims[1] / 2 - 12, ret['message'],
                curses.color_pair(color) | curses.A_BOLD)
            end_menu_call(var_dict["main_window"], 10)
        else:
            group_obj_class = str(object_classes_list[choice - 1])
            configuration_dict["group_object_class"] = group_obj_class
        end_message = "{group_ojbc} has been added to " \
                      "configuration.".format(group_ojbc=group_obj_class)
        var_dict["main_window"].addstr(screen_dims[0] / 2 - 4,
                                       screen_dims[1] / 2 - len(
                                           end_message) / 2,
                                       end_message,
                                       curses.color_pair(6) |
                                       curses.A_BOLD)
        show_console_in_status_window()
        menu_options[9] = u"10. Show List of Group Related ObjectClasses ✓"
        menu_color[9] = curses.color_pair(7)
        end_menu_call(var_dict["main_window"], 10)
    else:
        menu_color[9] = curses.color_pair(3)
        err_msg = "Unable to retrieve group object classes"
        var_dict["main_window"].addstr(
            screen_dims[0] / 2 - 2,
            screen_dims[1] / 2 - len(err_msg) / 2, err_msg,
            curses.color_pair(3) | curses.A_BOLD)
        end_menu_call(var_dict["main_window"], 10)


def menu_check_group_tree_dn_show_groups():
    screen_dims = setup_menu_call(
        var_dict["main_window"],
        "11. Check Group Tree DN and Show List of Groups")
    if check_group_config_dict(screen_dims):
        conn = var_dict["conn_info"]["conn"]
        group_dn = configuration_dict["group_tree_dn"]
        group_id_attribute = configuration_dict["group_id_attribute"]
        object_class = configuration_dict["group_object_class"]
        maximum = screen_dims[0] - screen_dims[0]/6 - 7
        limit_prompt = "How many groups would you like to see? Maximum: {" \
                       "max}".format(max=maximum)
        limit = my_numb_input(
            var_dict["main_window"],
            screen_dims[0]/6 + 4, screen_dims[1]/2 - len(limit_prompt)/2,
            limit_prompt)
        limit = min(limit, maximum)
        return_values = conn_service.list_entries(conn,
                                                  group_dn,
                                                  group_id_attribute,
                                                  object_class, limit)
    else:
        return_values = {"exit_status": 0}
    if return_values["exit_status"] == 1:
        LOG.info("Listing groups.")
        menu_options[10] = u"11. Check Group Tree DN and Show List of Groups ✓"
        menu_color[10] = curses.color_pair(7)
        list_of_groups = return_values["entries"]
        var_dict["list_of_groups"] = list_of_groups
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 6, 0, "List of "
                                                                  "Groups",
                                       curses.A_BOLD | curses.A_UNDERLINE)
        display_list_with_numbers_test(var_dict["main_window"],
                                       screen_dims[0] / 6 + 7, 0,
                                       list_of_groups)
        end_menu_call(var_dict["main_window"], 11)
    else:
        menu_color[10] = curses.color_pair(3)
        err_msg = "Unable to retrieve groups"
        var_dict["main_window"].addstr(screen_dims[0] / 2 - 2,
                                       screen_dims[1] / 2 - len(err_msg) / 2,
                                       err_msg,
                                       curses.color_pair(3) | curses.A_BOLD)
        end_menu_call(var_dict["main_window"], 11)


def menu_get_specific_group():
    screen_dims = setup_menu_call(var_dict["main_window"],
                                  "12. Get Specific Group")
    if check_group_config_dict(screen_dims):
        if "list_of_groups" not in var_dict:
            return menu_check_group_tree_dn_show_groups()
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 6, 0, "List of "
                                                                  "Groups",
                                       curses.A_BOLD | curses.A_UNDERLINE)
        display_list_with_numbers_test(var_dict["main_window"],
                                       screen_dims[0] / 6 + 7, 0,
                                       var_dict["list_of_groups"])
        conn = var_dict["conn_info"]["conn"]
        group_dn = configuration_dict["group_tree_dn"]
        group_id_attribute = configuration_dict["group_id_attribute"]
        object_class = configuration_dict["group_object_class"]
        group_name_attribute = configuration_dict["group_name_attribute"]
        name_msg_prompt = "What is the group name you would like to get?"
        name = my_raw_input(var_dict["main_window"], screen_dims[0] / 6 + 3,
                            screen_dims[1] / 2 - len(name_msg_prompt),
                            name_msg_prompt)
        return_values = conn_service.get_entry(conn, group_dn,
                                               group_id_attribute,
                                               object_class,
                                               group_name_attribute, name)
    else:
        return_values = {"exit_status": 0}
    if return_values["exit_status"] == 1:
        LOG.info("Getting specific group.")
        group = return_values["entry"]
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 5, 0, "Group: "
                                       "{grp}".format(grp=name),
                                       curses.A_UNDERLINE | curses.A_BOLD |
                                       curses.color_pair(8))
        display_list_with_numbers(var_dict["main_window"],
                                  screen_dims[0]/6 + 6,
                                  0, group)
        menu_options[11] = u"12. Get Specific Group ✓"
        menu_color[11] = curses.color_pair(7)
        end_menu_call(var_dict["main_window"], 12)
    else:
        menu_color[11] = curses.color_pair(3)
        err_msg = "Unable to retrieve group"
        var_dict["main_window"].addstr(screen_dims[0] / 2 - 2,
                                       screen_dims[1] / 2 - len(err_msg) / 2,
                                       err_msg,
                                       curses.color_pair(3) | curses.A_BOLD)
        end_menu_call(var_dict["main_window"], 12)


def menu_additional_config_options():
    LOG.info("Prompting for additional configuration options.")
    screen_dims = setup_menu_call(var_dict["main_window"],
                                  "13. Add Additional Configuration Options")

    use_tls_prompt = "What is use_tls? (True/False) Default: True"

    tls_req_cert_prompt = \
        "What is tls_req_cert? (demand/never/allow) Default: demand"

    use_pool_prompt = "What is use_pool? This is for LDAP connection " \
                      "pooling. (" \
                      "True/False)"

    use_auth_pool_prompt = "What is use_auth_pool? (True/False) Default: True"

    if "tls_cacertfile" in configuration_dict:
        use_tls_string = my_raw_input(
            var_dict["main_window"], screen_dims[0]/6 + 4,
            screen_dims[1]/2 - len(use_tls_prompt)/2, use_tls_prompt, True)
        if use_tls_string in ("True", "t", "T", "true"):
            use_tls_string = True
        elif use_tls_string in ("False", "false", "f", "F"):
            use_tls_string = False
        while use_tls_string not in (True, False):
            var_dict["main_window"].addstr(screen_dims[0]/6 + 5, screen_dims[
                1]/2 - len(use_tls_prompt)/2,
                                           "                                 ")
            use_tls_string = my_raw_input(
                var_dict["main_window"], screen_dims[0] / 6 + 4,
                screen_dims[1] / 2 - len(use_tls_prompt) / 2, use_tls_prompt,
                "True")
            if use_tls_string in ("True", "t", "T", "true"):
                use_tls_string = True
            elif use_tls_string in ("False", "false", "f", "F"):
                use_tls_string = False
    else:
        use_tls_prompt = "What is use_tls? (True/False) Default: False"
        use_tls_string = my_raw_input(
            var_dict["main_window"], screen_dims[0] / 6 + 4,
            screen_dims[1] / 2 - len(use_tls_prompt) / 2, use_tls_prompt,
            False)
        if use_tls_string in ("True", "t", "T", "true"):
            use_tls_string = True
        elif use_tls_string in ("False", "false", "f", "F"):
            use_tls_string = False
        while use_tls_string not in (True, False):
            var_dict["main_window"].addstr(screen_dims[0] / 6 + 5, screen_dims[
                1] / 2 - len(use_tls_prompt) / 2,
                                           "                                 ")
            use_tls_string = my_raw_input(
                var_dict["main_window"], screen_dims[0] / 6 + 4,
                screen_dims[1] / 2 - len(use_tls_prompt) / 2,
                use_tls_prompt,
                False)
            if use_tls_string in ("True", "t", "T", "true"):
                use_tls_string = True
            elif use_tls_string in ("False", "false", "f", "F"):
                use_tls_string = False
    configuration_dict["use_tls"] = use_tls_string
    show_console_in_status_window()

    tls_req_cert = my_raw_input(
        var_dict["main_window"], screen_dims[0] / 6 + 8,
        screen_dims[1] / 2 - len(tls_req_cert_prompt) / 2,
        tls_req_cert_prompt, "demand")
    while tls_req_cert not in ("demand", "allow", "never"):
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 9, screen_dims[
            1]/2 - len(tls_req_cert_prompt)/2,
                                       "                                  ")
        tls_req_cert = my_raw_input(
            var_dict["main_window"], screen_dims[0] / 6 + 8,
            screen_dims[1] / 2 - len(tls_req_cert_prompt) / 2,
            tls_req_cert_prompt, "demand")
    configuration_dict["tls_req_cert"] = tls_req_cert
    show_console_in_status_window()

    use_pool = my_raw_input(
        var_dict["main_window"], screen_dims[0] / 6 + 12,
        screen_dims[1] / 2 - len(use_pool_prompt) / 2,
        use_pool_prompt)
    if use_pool in ("True", "t", "T", "true"):
        use_pool = True
    elif use_pool in ("False", "false", "f", "F"):
        use_pool = False
    while use_pool not in (True, False):
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 13, screen_dims[
            1] / 2 - len(use_pool_prompt) / 2,
                                       "                                 ")
        use_pool = my_raw_input(
            var_dict["main_window"], screen_dims[0] / 6 + 12,
            screen_dims[1] / 2 - len(use_pool_prompt) / 2,
            use_pool_prompt)
        if use_pool in ("True", "t", "T", "true"):
            use_pool = True
        elif use_pool in ("False", "false", "f", "F"):
            use_pool = False
    configuration_dict["use_pool"] = use_pool
    show_console_in_status_window()

    use_auth_pool = my_raw_input(
        var_dict["main_window"], screen_dims[0] / 6 + 16,
        screen_dims[1] / 2 - len(use_auth_pool_prompt) / 2,
        use_auth_pool_prompt)
    if use_auth_pool in ("True", "t", "T", "true"):
        use_auth_pool = True
    elif use_auth_pool in ("False", "false", "f", "F"):
        use_auth_pool = False
    while use_auth_pool not in (True, False):
        var_dict["main_window"].addstr(screen_dims[0] / 6 + 17, screen_dims[
            1] / 2 - len(use_auth_pool_prompt) / 2,
                                       "                                 ")
        use_auth_pool = my_raw_input(
            var_dict["main_window"], screen_dims[0] / 6 + 16,
            screen_dims[1] / 2 - len(use_auth_pool_prompt) / 2,
            use_auth_pool_prompt)
        if use_auth_pool in ("True", "t", "T", "true"):
            use_auth_pool = True
        elif use_auth_pool in ("False", "false", "f", "F"):
            use_auth_pool = False
    configuration_dict["use_auth_pool"] = use_auth_pool
    show_console_in_status_window()

    menu_color[12] = curses.color_pair(7)
    menu_options[12] = u"13. Add Additional Configuration Options ✓"
    end_menu_call(var_dict["main_window"], 13)


def menu_create_config():
    screen_dims = setup_menu_call(var_dict["main_window"],
                                  "14. Save/Create Configuration File")
    data = configuration_dict
    string_prompt = "Please specify a file name."
    path = my_raw_input(var_dict["main_window"], screen_dims[0]/2,
                        screen_dims[1]/2 - len(string_prompt)/2, string_prompt)
    return_values = conn_service.save_config(data, path)
    if return_values["exit_status"] == 1:
        menu_options[13] = u"14. Save/Create Configuration File ✓"
        menu_color[13] = curses.color_pair(7)
    else:
        menu_color[13] = curses.color_pair(3)
    return_msg = return_values["message"]
    var_dict["main_window"].addstr(screen_dims[0]/2 - 4,
                                   screen_dims[1]/2 - len(return_msg)/2,
                                   return_msg)
    end_msg = "Press m to go to the menu."
    var_dict["main_window"].addstr(screen_dims[0]/2 - 3,
                                   screen_dims[1]/2 - len(end_msg)/2, end_msg)
    c = var_dict["main_window"].getch()
    while c != 109:
        if c == curses.KEY_RESIZE:
            resize_windows()
        c = var_dict["main_window"].getch()
    if c == 109:
        display_menu()


def display_menu():
    """Displays the menu. Does most of the work for displaying options."""
    stdscr_screen_dimensions = stdscr.getmaxyx()
    screen = stdscr.subwin(stdscr_screen_dimensions[0] - 2,
                           stdscr_screen_dimensions[1] -
                           stdscr_screen_dimensions[1] / 3 - 1,
                           1, 1)
    screen.keypad(True)
    screen_dimensions = screen.getmaxyx()
    screen_half_y = screen_dimensions[0]/2
    screen_half_x = screen_dimensions[1]/2
    screen.nodelay(0)
    screen.clear()
    var_dict["status_window"].box()
    show_console_in_status_window()
    screen.refresh()

    menu_selection = -1
    option_num = 0
    while menu_selection < 0:
        menu_highlighting = [0] * 15  # number of menu options
        menu_highlighting[option_num] = curses.A_STANDOUT
        screen.addstr(screen_half_y - 9, screen_half_x - 11,
                      "LDAP Configuration Menu", curses.A_UNDERLINE |
                      curses.color_pair(1) | curses.A_BOLD)
        screen.addstr(screen_half_y - 6, screen_half_x - 25,
                      menu_options[0].encode("utf-8"),
                      menu_highlighting[0] | menu_color[0])
        screen.addstr(screen_half_y - 5, screen_half_x - 25,
                      menu_options[1].encode("utf-8"),
                      menu_highlighting[1] | menu_color[1])
        screen.addstr(screen_half_y - 4, screen_half_x - 25,
                      menu_options[2].encode("utf-8"),
                      menu_highlighting[2] | menu_color[2])
        screen.addstr(screen_half_y - 3, screen_half_x - 25,
                      menu_options[3].encode("utf-8"),
                      menu_highlighting[3] | menu_color[3])
        screen.addstr(screen_half_y - 2, screen_half_x - 25,
                      menu_options[4].encode("utf-8"),
                      menu_highlighting[4] | menu_color[4])
        screen.addstr(screen_half_y - 1, screen_half_x - 25,
                      menu_options[5].encode("utf-8"),
                      menu_highlighting[5] | menu_color[5])
        screen.addstr(screen_half_y + 0, screen_half_x - 25,
                      menu_options[6].encode("utf-8"),
                      menu_highlighting[6] | menu_color[6])
        screen.addstr(screen_half_y + 1, screen_half_x - 25,
                      menu_options[7].encode("utf-8"),
                      menu_highlighting[7] | menu_color[7])
        screen.addstr(screen_half_y + 2, screen_half_x - 25,
                      menu_options[8].encode("utf-8"),
                      menu_highlighting[8] | menu_color[8])
        screen.addstr(screen_half_y + 3, screen_half_x - 25,
                      menu_options[9].encode("utf-8"),
                      menu_highlighting[9] | menu_color[9])
        screen.addstr(screen_half_y + 4, screen_half_x - 25,
                      menu_options[10].encode("utf-8"),
                      menu_highlighting[10] | menu_color[10])
        screen.addstr(screen_half_y + 5, screen_half_x - 25,
                      menu_options[11].encode("utf-8"),
                      menu_highlighting[11] | menu_color[11])
        screen.addstr(screen_half_y + 6, screen_half_x - 25,
                      menu_options[12].encode("utf-8"),
                      menu_highlighting[12] | menu_color[12])
        screen.addstr(screen_half_y + 7, screen_half_x - 25,
                      menu_options[13].encode("utf-8"),
                      menu_highlighting[13] | menu_color[13])
        screen.addstr(screen_half_y + 8, screen_half_x - 25, "15. Exit",
                      menu_highlighting[14] | curses.color_pair(3))
        screen.refresh()
        key_press = screen.getch()
        if key_press == curses.KEY_RESIZE:
            stdscr.clear()
            screen.clear()
            screen_dimensions = stdscr.getmaxyx()
            screen = stdscr.subwin(screen_dimensions[0] - 2,
                                   screen_dimensions[1] -
                                   screen_dimensions[1] / 3 - 1,
                                   1, 1)
            screen.keypad(True)
            main_screen_dimensions = screen.getmaxyx()
            screen_half_y = main_screen_dimensions[0]/2
            screen_half_x = main_screen_dimensions[1]/2
            resize_windows()
            stdscr.refresh()
            screen.refresh()
            status_window.refresh()
            status_window_text.refresh()
        elif key_press == curses.KEY_UP:
            option_num = (option_num - 1) % 15
        elif key_press == curses.KEY_DOWN:
            option_num = (option_num + 1) % 15
        elif key_press == ord('\n'):
            menu_selection = option_num
            if option_num == 0:
                menu_ping_ldap_ip()
            elif option_num == 1:
                menu_check_ldap_connection_adv()
            elif option_num == 2:
                menu_get_server_info()
            elif option_num == 3:
                menu_check_ldap_suffix()
            elif option_num == 4:
                menu_input_user_attributes()
            elif option_num == 5:
                menu_show_list_user_object_classes()
            elif option_num == 6:
                menu_check_user_tree_dn_show_users()
            elif option_num == 7:
                menu_get_specific_user()
            elif option_num == 8:
                menu_input_group_attributes()
            elif option_num == 9:
                menu_show_list_group_object_classes()
            elif option_num == 10:
                menu_check_group_tree_dn_show_groups()
            elif option_num == 11:
                menu_get_specific_group()
            elif option_num == 12:
                menu_additional_config_options()
            elif option_num == 13:
                menu_create_config()
            elif option_num == 14:
                if var_dict["conn_info"] != "none":
                    var_dict["conn_info"]["conn"].unbind()
                sys.exit(0)
            else:
                display_menu()
    curses.curs_set(1)


curses.wrapper(show_instructions)
curses.endwin()
