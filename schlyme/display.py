#!/usr/bin/python
# -*- coding: utf-8 -*-

class Color:
    RED            = u'\u001b[38;5;1m'
    GREEN          = u'\u001b[38;5;2m'
    YELLOW         = u'\u001b[38;5;3m'
    BLUE           = u'\u001b[38;5;4m'
    MAGENTA        = u'\u001b[38;5;5m'
    CYAN           = u'\u001b[38;5;6m'
    WHITE          = u'\u001b[38;5;7m'
    GRAY           = u'\u001b[38;5;8m'
    SALMON         = u'\u001b[38;5;9m'
    GREEN_BRIGHT   = u'\u001b[38;5;10m'
    YELLOW_BRIGHT  = u'\u001b[38;5;11m'
   #BLUE_BRIGHT    = u'\u001b[38;5;12m' # Same as BLUE
    MAGENTA_BRIGHT = u'\u001b[38;5;13m'
    CYAN_BRIGHT    = u'\u001b[38;5;14m'
   #WHITE_BRIGHT   = u'\u001b[38;5;15m' # Same as BOLD
    BOLD           = '\033[1m'
    UNDERLINE      = '\033[4m'
    PLAIN          = u'\u001b[0m'
    
    @classmethod
    def to_string(cls):
        return cls.BLUE           + 'BLUE'           + cls.PLAIN + '\n' \
             + cls.CYAN           + 'CYAN'           + cls.PLAIN + '\n' \
             + cls.CYAN_BRIGHT    + 'CYAN BRIGHT'    + cls.PLAIN + '\n' \
             + cls.GRAY           + 'GRAY'           + cls.PLAIN + '\n' \
             + cls.MAGENTA        + 'MAGENTA'        + cls.PLAIN + '\n' \
             + cls.MAGENTA_BRIGHT + 'MAGENTA BRIGHT' + cls.PLAIN + '\n' \
             + cls.RED            + 'RED'            + cls.PLAIN + '\n' \
             + cls.GREEN          + 'GREEN'          + cls.PLAIN + '\n' \
             + cls.GREEN_BRIGHT   + 'GREEN BRIGHT'   + cls.PLAIN + '\n' \
             + cls.SALMON         + 'SALMON'         + cls.PLAIN + '\n' \
             + cls.YELLOW         + 'YELLOW'         + cls.PLAIN + '\n' \
             + cls.YELLOW_BRIGHT  + 'YELLOW BRIGHT'  + cls.PLAIN + '\n' \
             + cls.WHITE          + 'WHITE'          + cls.PLAIN + '\n' \
             + cls.BOLD           + 'BOLD'           + cls.PLAIN + '\n' \
             + cls.UNDERLINE      + 'UNDERLINE'      + cls.PLAIN + '\n' \
             + cls.PLAIN          + 'PLAIN'          + cls.PLAIN
    
    @classmethod
    def print_all_colors(cls):
        for i in range(0, 16):
            for j in range(0, 16):
                code = str(i * 16 + j)
                print u"\u001b[38;5;" + code + "m " + code.ljust(4) + Color.PLAIN

