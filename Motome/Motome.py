"""
Motomoe is a note taking application inspired by Notational Velocity, ResophNotes and nvPY. Some of its features are:

 - Markdown rendering
 - History tracking
 - Note tagging
 - Note search and creation from a single input
 - Note merging & export
 - Auto-saves notes in the background
 - Cross-platform (Windows 7 and OS X 10.6 have been tested)

Released under the Simplified BSD licence.  Please see the LICENSE file.

@author: Aaron Kehrer

The latest issues and enhancements should be at the following link:
https://github.com/akehrer/Motome/issues
"""

# Import standard library modules
import sys

# Import Qt modules
from PySide import QtGui

# Import app modules
from Modules.MainWindow import MainWindow


__version__ = "0.1.0"


class App(QtGui.QApplication):
    def __init__(self, *args):
        QtGui.QApplication.__init__(self, *args)
        self.main = MainWindow()
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
