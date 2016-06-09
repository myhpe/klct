import curses

term_screen = curses.initscr() # terminal screen
term_screen_dimensions = term_screen.getmaxyx()
term_screen.keypad(True)
curses.noecho()
start_instruction = "Needs to be implemented. Press any key to go to the menu"


def show_instructions(screen):
    curses.curs_set(0)
    screen_dimensions = screen.getmaxyx()
    screen.clear()
    screen.addstr(screen_dimensions[0]/2,
                       screen_dimensions[1]/2 - len(start_instruction)/2, start_instruction)
    screen.getch()
    display_menu(screen)


def menu_ping_ldap_ip(screen):
    screen.clear()
    my_raw_input(screen, 0, 0, "Enter IP")


def my_raw_input(screen, y, x, prompt_string):
    curses.echo()
    screen.addstr(y, x, prompt_string)
    screen.refresh()
    str_input = screen.getstr(y + 1, x, 20)
    return str_input


def display_menu(screen):
    screen_dimensions = screen.getmaxyx()
    screen_half_y = screen_dimensions[0]/2
    screen_half_x = screen_dimensions[1]/2
    screen.nodelay(0)
    screen.clear()
    menu_selection = -1
    menu_options = ["Ping LDAP Server IP", "Check Connection to LDAP Server", "Get Server Information",
                    "Check LDAP Suffix", "Show List of User-Related ObjectClasses",
                    "Check User Tree DN and Show List of Users", "Get a Specific User",
                    "Show List of Group Related ObjectClasses", "Check Group Tree DN and Show List of Groups",
                    "Get Specific Group", "Add Additional Configuration Options",
                    "Show Configuration", "Save/Create Configuration File"]
    option_num = 0
    while menu_selection < 0:
        menu_highlighting = [0] * 13 # 3 == number of menu options
        menu_highlighting[option_num] = curses.A_REVERSE
        screen.addstr(0, screen_half_x - 2, "MENU", curses.A_BOLD)
        screen.addstr(screen_half_y - 6, screen_half_x - len(menu_options[0])/2, menu_options[0], menu_highlighting[0])
        screen.addstr(screen_half_y - 5, screen_half_x - len(menu_options[1])/2, menu_options[1], menu_highlighting[1])
        screen.addstr(screen_half_y - 4, screen_half_x - len(menu_options[2])/2, menu_options[2], menu_highlighting[2])
        screen.addstr(screen_half_y - 3, screen_half_x - len(menu_options[3])/2, menu_options[3], menu_highlighting[3])
        screen.addstr(screen_half_y - 2, screen_half_x - len(menu_options[4])/2, menu_options[4], menu_highlighting[4])
        screen.addstr(screen_half_y - 1, screen_half_x - len(menu_options[5])/2, menu_options[5], menu_highlighting[5])
        screen.addstr(screen_half_y + 0, screen_half_x - len(menu_options[6])/2, menu_options[6], menu_highlighting[6])
        screen.addstr(screen_half_y + 1, screen_half_x - len(menu_options[7])/2, menu_options[7], menu_highlighting[7])
        screen.addstr(screen_half_y + 2, screen_half_x - len(menu_options[8])/2, menu_options[8], menu_highlighting[8])
        screen.addstr(screen_half_y + 3, screen_half_x - len(menu_options[9])/2, menu_options[9], menu_highlighting[9])
        screen.addstr(screen_half_y + 4, screen_half_x - len(menu_options[10])/2, menu_options[10], menu_highlighting[10])
        screen.addstr(screen_half_y + 5, screen_half_x - len(menu_options[11])/2, menu_options[11], menu_highlighting[11])
        screen.addstr(screen_half_y + 6, screen_half_x - 2, "Exit", menu_highlighting[12])

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

    curses.curs_set(1)

curses.wrapper(show_instructions)
curses.endwin()