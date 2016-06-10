# -*- coding: utf-8 -*-
import curses
import locale
import sys
sys.path.insert(0, '../ldap')
import configTool


"""SET UP"""
locale.setlocale(locale.LC_ALL,"")  # for unicode support
term_screen = curses.initscr()  # terminal screen
term_screen_dimensions = term_screen.getmaxyx()  # returns tuple (y,x) of current screen resolution
term_screen.keypad(True)  # enables arrow keys and multi-byte sequences i.e.(f1-f12,page up, page down)
curses.noecho()
start_instruction = "LDAP Configuration Tool. Press 'm' to go to the menu."
if curses.has_colors():  # enable coloring
    curses.start_color()
curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_WHITE)
curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)
curses.init_pair(7, curses.COLOR_GREEN, curses.COLOR_WHITE)
term_screen.bkgd(curses.color_pair(1))

"""VARS THAT MIGHT CHANGE DURING EXECUTION OF PROGRAM"""
menu_color = [curses.color_pair(2)] * 12  # number of menu options = 12
menu_options = ["Ping LDAP Server IP",
                "Check Connection to LDAP Server",
                "Get Server Information",
                "Check LDAP Suffix",
                "Show List of User-Related ObjectClasses",
                "Check User Tree DN and Show List of Users",
                "Get a Specific User",
                "Show List of Group Related ObjectClasses",
                "Check Group Tree DN and Show List of Groups",
                "Get Specific Group",
                "Add Additional Configuration Options",
                "Show Configuration",
                "Save/Create Configuration File"]
valid_ip_addr = [0]  # string value of IP address, set to false (0) until successful pinging of IP address


"""HELPER METHODS"""


def show_instructions(screen):
    """Displays the starting instructions prior to the menu display."""
    curses.curs_set(0)
    screen_dimensions = screen.getmaxyx()
    screen.clear()
    char_press = 0
    screen.addstr(screen_dimensions[0]/2,
                  screen_dimensions[1]/2 - len(start_instruction)/2, start_instruction)
    while char_press != ord('m'):
        char_press = screen.getch()
    display_menu(screen)


def my_raw_input(screen, y, x, prompt_string):
    """Prompt for input from user. Given a (y, x) coordinate,
    will show a prompt at (y + 1, x). Currently only able to
    prompt for 20 chars, but can change later."""
    curses.echo() # so user can see
    screen.addstr(y, x, prompt_string, curses.color_pair(2))
    screen.addch(y + 1, x, ">")
    screen.refresh()
    str_input = screen.getstr(y + 1, x + 1, 20)  # 20 = max chars to in string
    curses.noecho()
    return str_input


"""MAIN METHODS"""


def menu_ping_ldap_ip(screen):
    """Displays a screen prompting user for IP address and then
    pings that IP address to see if it able to send a response."""
    success = "Successfully pinged given IP address."
    fail = "Unsuccessfully pinged given IP address."
    screen.clear()
    temp_char = 0
    screen_dims = screen.getmaxyx()

    ip_string = my_raw_input(screen, screen_dims[0] / 2, screen_dims[1] / 2 - 23,
                             "Please Enter the IP Address of the LDAP server.")
    screen.addstr(screen_dims[0] / 2 + 2, screen_dims[1] / 2 - 12, "Attempting to ping IP...",
                  curses.color_pair(5) | curses.A_BLINK)
    screen.refresh()
    temp_bool = configTool.ping_LDAP_server(ip_string)
    if temp_bool == 1 and ip_string != "":
        screen.addstr(screen_dims[0] / 2 + 4, screen_dims[1] / 2 - len(success) / 2,
                      success, curses.color_pair(6))
        screen.addstr(screen_dims[0] / 2 + 5, screen_dims[1] / 2 - 26,
                      "This IP will automatically be used in the next step.", curses.color_pair(4))
        screen.addstr(screen_dims[0] / 2 + 6, screen_dims[1] / 2 - 25,
                      "Press 'n' to move on to next step, or 'm' for menu.")
        menu_options[0] = u"Ping LDAP Server IP ✓"
        menu_color[0] = curses.color_pair(7)
        valid_ip_addr[0] = ip_string
    elif temp_bool == -1:
        screen.addstr(screen_dims[0] / 2 + 4, screen_dims[1] / 2 - 23, "Invalid Hostname or IP. Press 'r' to retry.",
                      curses.color_pair(3))
    else:
        screen.addstr(screen_dims[0] / 2 + 4, screen_dims[1] / 2 - len(fail) / 2, fail, curses.color_pair(3))
        screen.addstr(screen_dims[0] / 2 + 5, screen_dims[1] / 2 - 18,
                      "Press 'r' to retry this step, or 'm' for menu.")
    while temp_char not in (110, 109, 114):  # 109 = 'm', 110 = 'n', 114 = 'r'
        temp_char = screen.getch()
    if temp_char == 109:
        display_menu(screen)
    elif temp_char == 110:
        menu_check_ldap_connection_basic(screen)
    elif temp_char == 114:
        menu_ping_ldap_ip(screen)


def menu_check_ldap_connection_basic(screen):
    """The method that handles the 'Check Connections to LDAP Server' option."""
    screen.clear()
    screen_dims = screen.getmaxyx()
    key_press = 0
    if valid_ip_addr[0] == 0:
        screen.addstr(screen_dims[0] / 2 - 4, screen_dims[1] / 2 - 26,
                      "No valid IP found. Please complete the previous step", curses.A_BOLD | curses.color_pair(3))
        screen.addstr(screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 23,
                      "Press p to go to previous step, or 'm' for menu", curses.color_pair(5))
        while key_press not in (109, 112):  # 109 == m, 112 == p
            key_press = screen.getch()
        if key_press == 109:
            display_menu(screen)
        elif key_press == 112:
            menu_ping_ldap_ip(screen)
    else:
        host_ip = valid_ip_addr[0]
        temp_str = my_raw_input(screen, screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 22,
                                "Please enter the port number. Default is 389.")
        while not temp_str.isdigit():
            screen.clear()
            temp_str = my_raw_input(screen, screen_dims[0] / 2 - 3, screen_dims[1] / 2 - 30,
                                    "Input entered is not a valid port number. Please retry.")
        port_numb = int(temp_str)
        screen.addstr(screen_dims[0] / 2, screen_dims[1] / 2 - 18, "Attempting to connect to LDAP server",
                      curses.color_pair(5))
        screen.refresh()
        triple = configTool.connect_LDAP_server_basic(host_ip, port_numb)
        if triple[0] == 1:
            screen.addstr(screen_dims[0] / 2 + 1, screen_dims[1] / 2 - len(triple[1]) / 2, triple[1],
                          curses.color_pair(6) | curses.A_BOLD)
            menu_options[1] = u"Check Connection to LDAP ✓"
            menu_color[1] = curses.color_pair(7)
            screen.addstr(screen_dims[0] / 2 + 6, screen_dims[1] / 2 - 25,
                          "Press 'n' to move on to next step, or 'm' for menu.")

            character = screen.getch()
            while character not in (109, 110):
                character = screen.getch()
            if character == 109:
                display_menu(screen)
            elif character == 110:
                print("FIX MEEEEEEEEEE")
        else:
            screen.addstr(screen_dims[0] / 2 + 1, screen_dims[1] / 2 - len(triple[1]) / 2, triple[1],
                          curses.color_pair(3) | curses.A_BOLD)

            print("FIX MEEEEEEEEEEEEE")



def menu_check_ldap_connection_adv(screen):
    print("NEEDS IMPLEMENTATION")


def menu_get_server_info(screen):
    print("NEEDS IMPLEMENTATION")


def menu_check_ldap_suffix(screen):
    print("NEEDS IMPLEMENTATION")


def menu_show_list_user_object_classes(screen):
    print("NEEDS IMPLEMENTATION")


def menu_check_user_tree_dn_show_users(screen):
    print("NEEDS IMPLEMENTATION")


def menu_get_specific_user(screen):
    print("NEEDS IMPLEMENTATION")


def menu_show_list_group_object_classes(screen):
    print("NEEDS IMPLEMENTATION")


def menu_check_group_tree_dn_show_groups(screen):
    print("NEEDS IMPLEMENTATION")


def menu_get_specific_group(screen):
    print("NEEDS IMPLEMENTATION")


def menu_additional_config_options(screen):
    print("NEEDS IMPLEMENTATION")


def menu_show_config(screen):
    print("NEEDS IMPLEMENTATION")


def menu_create_config(screen):
    print("NEEDS IMPLEMENTATION")


def display_menu(screen):
    """Displays the menu. Does most of the work for displaying options."""
    screen_dimensions = screen.getmaxyx()
    screen_half_y = screen_dimensions[0]/2
    screen_half_x = screen_dimensions[1]/2
    screen.nodelay(0)
    screen.clear()
    menu_selection = -1
    option_num = 0
    while menu_selection < 0:
        menu_highlighting = [0] * 13 # number of menu options
        menu_highlighting[option_num] = curses.A_STANDOUT
        screen.addstr(0, screen_half_x - 11,
                      "LDAP Configuration Menu",curses.A_UNDERLINE | curses.color_pair(1) | curses.A_BOLD)
        screen.addstr(screen_half_y - 6, screen_half_x - len(menu_options[0])/2,
                      menu_options[0].encode("utf-8"), menu_highlighting[0] | menu_color[0])
        screen.addstr(screen_half_y - 5, screen_half_x - len(menu_options[1])/2,
                      menu_options[1].encode("utf-8"), menu_highlighting[1] | menu_color[1])
        screen.addstr(screen_half_y - 4, screen_half_x - len(menu_options[2])/2,
                      menu_options[2].encode("utf-8"), menu_highlighting[2] | menu_color[2])
        screen.addstr(screen_half_y - 3, screen_half_x - len(menu_options[3])/2,
                      menu_options[3].encode("utf-8"), menu_highlighting[3] | menu_color[3])
        screen.addstr(screen_half_y - 2, screen_half_x - len(menu_options[4])/2,
                      menu_options[4].encode("utf-8"), menu_highlighting[4] | menu_color[4])
        screen.addstr(screen_half_y - 1, screen_half_x - len(menu_options[5])/2,
                      menu_options[5].encode("utf-8"), menu_highlighting[5] | menu_color[5])
        screen.addstr(screen_half_y + 0, screen_half_x - len(menu_options[6])/2,
                      menu_options[6].encode("utf-8"), menu_highlighting[6] | menu_color[6])
        screen.addstr(screen_half_y + 1, screen_half_x - len(menu_options[7])/2,
                      menu_options[7].encode("utf-8"), menu_highlighting[7] | menu_color[7])
        screen.addstr(screen_half_y + 2, screen_half_x - len(menu_options[8])/2,
                      menu_options[8].encode("utf-8"), menu_highlighting[8] | menu_color[8])
        screen.addstr(screen_half_y + 3, screen_half_x - len(menu_options[9])/2,
                      menu_options[9].encode("utf-8"), menu_highlighting[9] | menu_color[9])
        screen.addstr(screen_half_y + 4, screen_half_x - len(menu_options[10])/2,
                      menu_options[10].encode("utf-8"), menu_highlighting[10] | menu_color[10])
        screen.addstr(screen_half_y + 5, screen_half_x - len(menu_options[11])/2,
                      menu_options[11].encode("utf-8"), menu_highlighting[11] | menu_color[11])
        screen.addstr(screen_half_y + 6, screen_half_x - 2, "Exit",
                      menu_highlighting[12] | curses.color_pair(3))
        screen.refresh()

        key_press = screen.getch()
        if key_press == curses.KEY_UP:
            option_num = (option_num - 1) % 13
        elif key_press == curses.KEY_DOWN:
            option_num = (option_num + 1) % 13
        elif key_press == ord('\n'):
            menu_selection = option_num
            if option_num == 0:
                menu_ping_ldap_ip(screen)
            elif option_num == 1:
                menu_check_ldap_connection_basic(screen)
            elif option_num == 12:
                break
            else:
                display_menu(screen)
    curses.curs_set(1)

curses.wrapper(show_instructions)
curses.endwin()
