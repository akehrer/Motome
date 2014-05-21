# Import the future
from __future__ import absolute_import

# Import standard library modules
import logging
import os
import sys

# Import Qt modules
from PySide import QtGui

# Import app modules
from Motome.Controllers.MainWindow import MainWindow

from Motome.config import LOG_LEVEL, APP_DIR

# Build the logger
logging.basicConfig(filename='motome.log',
                    filemode='a',
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    level=LOG_LEVEL)


class App(QtGui.QApplication):
    def __init__(self, *args):
        QtGui.QApplication.__init__(self, *args)

        if len(args[0]) > 1 and args[0][1] == 'portable':
        # the commandline args are passed to the class, check to see if the portable option is set
            self.main = MainWindow(portable=True)
        else:
            self.main = MainWindow()

        # Load custom fonts
        self.font_database = QtGui.QFontDatabase()
        font_name_dirs = ['Bright', 'Serif', 'Typewriter']
        for name in font_name_dirs:
            fontpath = os.path.join(APP_DIR, 'styles', 'default', 'fonts', name)
            for f in os.listdir(fontpath):
                if f.endswith(".ttf"):
                    p = os.path.join(fontpath, f)
                    self.font_database.addApplicationFont(p)

        self.lastWindowClosed.connect(self.byebye)
        self.main.show()
        self.main.raise_()

    def byebye(self):
        self.main.stop()
        self.exit(0)


def main():
    global app
    app = App(sys.argv)
    app.exec_()

if __name__ == "__main__":
    main()