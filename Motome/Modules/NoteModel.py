# Import the future
from __future__ import print_function
from __future__ import unicode_literals

from hashlib import md5
from os import stat, path

from Utils import safe_filename


class NoteModel(object):
    """
    The main note model contains useful information and name conversions for a given note
    """
    def __init__(self, filepath=None):
        self.filepath = filepath

    @property
    def filename(self):
        try:
            return path.basename(self.filepath)
        except AttributeError:
            return None

    @property
    def notename(self):
        try:
            return path.basename(path.splitext(self.filepath)[0])
        except AttributeError:
            return None

    @property
    def safename(self):
        return safe_filename(self.filename)

    @property
    def hashname(self):
        try:
            return md5(self.filepath).hexdigest()
        except AttributeError:
            return None

    @property
    def timestamp(self):
        try:
            return stat(self.filepath).st_mtime
        except AttributeError:
            return None

    def __str__(self):
        return '<Note: {0}, Last Modified: {1}>'.format(self.notename, self.timestamp)
