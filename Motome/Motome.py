# Import standard library modules
import logging
import os
import sys

# Import Qt modules
from PySide import QtGui

# Import app modules
from Modules.MainWindow import MainWindow

from config import LOG_LEVEL, APP_DIR

# Build the logger
logging.basicConfig(filename='motome.log',
                    filemode='a',
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    level=LOG_LEVEL)


class App(QtGui.QApplication):
    def __init__(self, *args):
        QtGui.QApplication.__init__(self, *args)
        self.main = MainWindow()

        # Load custom fonts
        self.font_database = QtGui.QFontDatabase()
        font_name_dirs = ['Bright', 'Serif', 'Typewriter']
        for name in font_name_dirs:
            fontpath = os.path.join(APP_DIR, 'styles', 'default', 'fonts', name)
            for file in os.listdir(fontpath):
                if file.endswith(".ttf"):
                    p = os.path.join(fontpath, file)
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
