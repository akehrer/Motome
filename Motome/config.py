# Import the future
from __future__ import unicode_literals

VERSION = '0.2.3'

# Import standard library modules
import logging
import os
import sys

# Import Qt modules
from PySide.QtGui import QColor

PLATFORM = sys.platform

LOG_LEVEL = logging.DEBUG

###################################################
#       Motome Configuration Variables            #
###################################################

# app directory, determine if application is a script file or frozen exe
# see: http://stackoverflow.com/questions/404744/determining-application-path-in-a-python-exe-generated-by-pyinstaller
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
elif __file__:
    APP_DIR = os.path.dirname(__file__)

# window title prefix
WINDOW_TITLE = 'Motome'  # 'Mo\u0305to\u0305me'

# Default notes directory if the user never chooses one, this will be created in their home directory
DEFAULT_NOTES_DIR = "Notes"

# app data directory in note directory
NOTE_DATA_DIR = '.motome'

# file extensions
NOTE_EXTENSION = '.txt'
ZIP_EXTENSION = '.zip'
HTML_EXTENSION = '.html'

# file encoding
ENCODING = 'utf-8'

# note directory sub-folder names
MEDIA_FOLDER = 'media'
HTML_FOLDER = 'html'
HISTORY_FOLDER = 'archive'

# the character prepended to tag values when searching
TAG_QUERY_CHAR = '#'

# unsafe filename characters, being pretty strict
UNSAFE_CHARS = '<>:"/\|?*#'

# the unicode end of text character
# http://www.fileformat.info/info/unicode/char/0003/index.htm
# This signifies where the note content ends and any metadata begins
END_OF_TEXT = '\u0003'  # Only applies to pre 0.2 versions

# the YAML bracket that splits the files metadata
YAML_BRACKET = '---'

# colors
MOTOME_BLUE = QColor.fromRgb(38, 87, 127, a=255)
MOTOME_LTBLUE = QColor.fromRgb(145, 177, 203, a=255)
MOTOME_GRYBLUE = QColor.fromRgb(89, 122, 148, a=255)
MOTOME_BRTBLUE = QColor.fromRgb(61, 139, 203, a=255)
HIGHLIGHT_COLOR = QColor.fromRgb(255, 255, 153, a=255)

# diff status template, to show when at current note record
STATUS_TEMPLATE = """
<html>
    <body>
        <p>
            {notename}
        </p>
        <p>
            This is the latest version.
        </p>
        <p>
            Last saved: {timestamp}
        </p>
        <p>
            Last Recorded: {recorded}
        </p>
    </body>
</html>"""
