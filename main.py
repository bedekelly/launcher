#!/usr/bin/python3

import curses
import curses.panel
import sys
import os
import re
from time import sleep
from enum import Enum
from contextlib import contextmanager

WHOLE_PATTERN_FIRST = 4
WHOLE_PATTERN_IN_STRING = 3
PATTERN_IN_STRING = 2
PATTERN_NOT_FOUND = 1


class keys:
    CTRL_D = 4
    TAB = 9
    ALT_BACKSPACE = 27
    BACKSPACE = 127
    RETURN = 10
    ESCAPE = -1


def memoize(fn):
    dictionary = {}
    def new_func(*args):
        try:
            return dictionary[args]
        except KeyError:
            dictionary[args] = fn(*args)
            return dictionary[args]
    return new_func


def parse_menu(menufile_text):
    """Parse debian menu files to return name and data for a program."""
    def make_dict(matches):
        data_dict = {}
        for key, value in matches:
            data_dict[key] = value
        return data_dict

    name_match = re.search("\?package\((.*?)\)", menufile_text)
    property_matches = re.findall("(\w+)=\"(.*?)\"", menufile_text)
    try:
        name = name_match.group(1)
        data = make_dict(property_matches)
        return name, data
    except AttributeError:
        return None, None


@memoize
def get_programs():
    """Returns a dictionary of program names and their associated data."""
    programs = {}
    path = "/usr/share/menu/"
    for filename in os.listdir(path=path):
        with open(os.path.join(path, filename)) as menufile:
            name, data = parse_menu(menufile.read())
            if name and data:
                programs[name] = data
    return programs


@contextmanager
def use_curses():
    """Wrapper for the uglier bits of curses initialization."""
    try:
        # Set up a curses window and yield it
        stdscr = curses.initscr()
        for fn in [stdscr.clear,
                   stdscr.box,
                   lambda: curses.curs_set(0),
                   curses.cbreak,
                   curses.noecho,
                   stdscr.refresh]:
            fn()
        yield stdscr
    finally:
        # Cleanup the curses window
        for fn in [curses.cbreak,
                   curses.echo,
                   stdscr.clear,
                   curses.endwin]:
            fn()


def fuzzy_search(pattern, string, first_iteration=True):
    """Returns one of four values indicating how well the pattern matches."""
    string = string.lower()
    pattern = pattern.lower()
    if pattern in string:
        if first_iteration:
            if string.index(pattern) == 0:
                return WHOLE_PATTERN_FIRST
            else:
                return WHOLE_PATTERN_IN_STRING
        else:
            return PATTERN_IN_STRING
    elif pattern[0] in string:
        charpos = string.index(pattern[0])
        return fuzzy_search(pattern[1:],
                            string[charpos+1:],
                            first_iteration=False)
    else:
        return PATTERN_NOT_FOUND


def matching_programs(pattern):
    """Generate programs matching a given pattern."""
    programs = get_programs()
    search_results = []

    # For every program, check if it matches by title or by filename.
    for program, data in programs.items():
        title_result = fuzzy_search(pattern, data['title'])
        filename_result = fuzzy_search(pattern, program)
        title_match = True
        for result in title_result, filename_result:
            if result in (WHOLE_PATTERN_FIRST,
                          WHOLE_PATTERN_IN_STRING,
                          PATTERN_IN_STRING):
                search_results.append((program, data, title_match, result))
                break
            title_match = False

    # Sort the programs by how well they matched and yield them.
    sorted_ = sorted(search_results, key=lambda r: r[3], reverse=True)
    for i, item in enumerate(sorted_):
        program, data, title_match, _ = item
        yield (program, data, title_match)


def log(obj):
    """A basic logging function."""
    with open("logfile", 'a') as file:
        file.write('\n{}'.format(obj))


def embolden(item, pattern=""):
    """Make certain letters in 'item' bold, based on the pattern that matches it."""
    def bold(char):
        return '[BOLD]' + char + '[/BOLD]'
    if pattern == "":
        return ' '.join(item)

    first_char = item.lower().index(pattern.lower()[0])
        
    first, char, second = item[:first_char], item[first_char], item[first_char+1:]
    first_bit = ' '.join(first)
    char = bold(char)
    second_bit = embolden(second, pattern=pattern[1:])
    return (first_bit + ' ' + char + ' ' + second_bit).strip()


# Wrap the 'all' function for aesthetics.
_all = all
def all(*args):
    return _all(list(args))


def cut_bolds(letter):
    """Remove complete or incomplete bold tags from a letter."""
    return (letter.replace("[BOLD]", "")
            .replace("[/BOLD]", "")
            .strip("/")
            .strip("["))

isbold = lambda letter: all(letter.startswith("[BOLD]"),
                            letter.endswith("[/BOLD]")) 


class Launcher:
    def __init__(self, stdscr):
        """Initialize the launcher."""
        self.stdscr = stdscr

        self.pattern = ""
        self.pad = 4
        self.running = True
        self.maxy, self.maxx = [i-self.pad for i in self.stdscr.getmaxyx()]
        self.selected_item = 0
        self.matches = []  # default, will be overwritten

    def run_current_selection(self):
        """Send the shell command to get the process running."""
        import subprocess
        name, data, _ = self.matches_copy[self.selected_item]
        if data["needs"] == "text":
            with open(os.devnull, "w") as devnull:
                subprocess.call(["nohup", "gnome-terminal", "-e",
                                 data["command"]],
                                stdout=devnull,
                                stderr=devnull)
        else:
            with open(os.devnull, "w") as devnull:
                subprocess.call(["nohup", data["command"]],
                                stdout=devnull,
                                stderr=devnull)
        quit()

    def handle_key(self, key):
        """Handle a keypress caught by curses."""
        # Test for special keys.
        if ord(key) == keys.BACKSPACE:
            if len(self.pattern) > 1:
                self.pattern = self.pattern[:-1]
            else:
                self.pattern = ""
        
        elif ord(key) == keys.CTRL_D:
            raise EOFError

        elif ord(key) == keys.ALT_BACKSPACE:
            try:
                pattern = ''.join(pattern.split()[:-1])
            except UnboundLocalError:
                pass
        elif ord(key) == keys.RETURN:
            self.run_current_selection()

        elif ord(key) == keys.TAB:
            self.next_selection()

        # Default to appending the key to the current pattern.
        else:
            self.selected_item = 0
            self.pattern += key

    def next_selection(self):
        if self.selected_item < self.maxy-self.pad:
            self.selected_item += 1

    def print_current_selection(self):
        if self.pattern:
            self.stdscr.addstr(self.pad + self.selected_item + 2, 1, "->")

    def print_separator(self):
        self.stdscr.addnstr(self.pad, self.pad, "-"*(self.maxx-self.pad), self.maxx)

    def update_xy(self):
        self.maxy, self.maxx = [i-self.pad for i in self.stdscr.getmaxyx()]

    def print_pattern(self):
        self.stdscr.addstr(self.pad-1, self.pad, self.pattern)

    def start(self):
        """Start the launcher's main loop."""
        self.print_separator()
        self.stdscr.box()

        box = curses.newwin(4, self.maxx-8, self.pad, self.pad)
        box.addstr(1,1,"hello")
        while self.running:
            # Enter the main program loop
            key = self.stdscr.getkey()
            for fn in [self.stdscr.clear,

                       lambda: self.handle_key(key),
                       self.update_xy,
                       self.print_pattern,
                       self.print_separator,
                       self.stdscr.box,
                       self.generate_menu_items,
                       self.print_menu_items,
                       self.print_current_selection,
                       self.stdscr.refresh]:
                fn()
            

    def print_menu_items(self):
        # Print current selection indicator
        self.matches_copy = []
        for word_index, program in enumerate(self.matches):
            self.matches_copy.append(program)
            program, data, name_match = program
            if word_index < (self.maxy - self.pad - 2):
                # Don't try to highlight the title if the user's pattern only matched the filename.
                if name_match:
                    letters = embolden(data['title'], self.pattern)
                else:
                    letters = data['title']
                    
                    # Print out each letter with its attributes.
                for letter_index, letter in enumerate(letters.split()):
                    if isbold(letter):
                        self.stdscr.addstr(word_index+self.pad+2, letter_index+self.pad,
                                           cut_bolds(letter),
                                           curses.A_BOLD)
                    else:
                        self.stdscr.addstr(word_index+self.pad+2, letter_index+self.pad, letter)
            else:  # Don't try to print things off the page.
                break
                self.stdscr.refresh()
                            
    def generate_menu_items(self):
        if self.pattern:
            # Get a list of programs which match the current pattern
            self.matches = matching_programs(self.pattern)
        else:
            self.matches = []

            
                            

def main():
    with use_curses() as stdscr:
        launcher = Launcher(stdscr)
        try:
            launcher.start()
        except (KeyboardInterrupt, EOFError):
            pass

if __name__ == "__main__":
    main()
