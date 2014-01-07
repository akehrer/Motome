# Import the future
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import hashlib
import os
import re
import zipfile

from Utils import enc_read, enc_write

from config import END_OF_TEXT, ZIP_EXTENSION, NOTE_EXTENSION


class NoteModel(object):
    """
    The main note model contains the note information and name conversions for a given note.
    """
    def __init__(self, filepath=None):
        self.filepath = filepath

        self._content = ''
        self._metadata = {}
        self._history = []
        self._last_seen = 0

    def __repr__(self):
        return '<Note: {0}, Last Modified: {1}>'.format(self.notename, self.timestamp)

    @property
    def content(self):
        if self.timestamp > self._last_seen:
            self._update_from_file()
        return self._content

    @content.setter
    def content(self, value):
        if value != self._content:
            self._content = value
            self._save_to_file()

    @property
    def metadata(self):
        if self.timestamp > self._last_seen:
            self._update_from_file()
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        if value != self._metadata:
            self._metadata = value
            self._save_to_file()

    @property
    def history(self):
        zip_filepath = self.filepath + ZIP_EXTENSION
        self._history = []
        with zipfile.ZipFile(zip_filepath, 'r') as myzip:
            self._history = sorted(myzip.namelist())
        return self._history

    @property
    def filename(self):
        try:
            return os.path.basename(self.filepath)
        except AttributeError:
            return None

    @property
    def notename(self):
        try:
            return os.path.basename(os.path.splitext(self.filepath)[0])
        except AttributeError:
            return None

    @property
    def safename(self):
        return self.safe_filename(self.notename)

    @property
    def unsafename(self):
        return self.safename.replace('_', ' ')

    @property
    def shortname(self):
        return self.safename[:4] + self.safename[-4:]

    @property
    def hashname(self):
        try:
            return hashlib.sha1(self.filepath.encode('UTF-8')).hexdigest()
        except AttributeError:
            return None

    @property
    def timestamp(self):
        try:
            return os.stat(self.filepath).st_mtime
        except:
            return None

    def load_old_note(self, index):
        try:
            zip_filepath = self.filepath + ZIP_EXTENSION
            with zipfile.ZipFile(zip_filepath, 'r') as myzip:
                old_content = unicode(myzip.read(self._history[index]))
                old_date = self._history[index][:-(len(ZIP_EXTENSION)+1)]
        except Exception as e:
            old_content = None
            old_date = None
        return old_content, old_date

    def record(self, notes_dir):
        """
        Write the old file data to the zip archive

        :param notes_dir:
        """
        now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        old_filename = now + NOTE_EXTENSION
        old_filepath = os.path.join(notes_dir, old_filename)

        self._save_to_file(filepath=old_filepath)

        zip_filepath = self.filepath + ZIP_EXTENSION
        with zipfile.ZipFile(zip_filepath, 'a') as myzip:
            myzip.write(old_filepath, old_filename)
        os.remove(old_filepath)

    def _update_from_file(self):
        self._content, self._metadata = self.parse_note_content(enc_read(self.filepath))
        self._last_seen = self.timestamp

    def _save_to_file(self, filepath=None):
        """
        Save the content and metadata to the note file
        """
        if filepath is None:
            filepath = self.filepath
        if not 'title' in self._metadata.keys():
            self._metadata['title'] = self.notename
        filedata = self._content + '\n' + END_OF_TEXT + '\n'
        for key, value in self._metadata.items():
                filedata = filedata + '{0}:{1}\n'.format(key, value)
        enc_write(filepath, filedata)


    @staticmethod
    def safe_filename(filename):
        """ Convert the filename into something more url safe

        :param filename:
        :return: safer filename or None on failure
        """
        try:
            pattern = re.compile('[\W_]+')  # find all words
            root, ext = os.path.splitext(os.path.basename(filename))
            return pattern.sub('_', root) if ext is '' else ''.join([pattern.sub('_', root), ext])
        except:
            return None

    @staticmethod
    def parse_note_content(data):
        """
        Given a file's data, split it into its note content and metadata.
        :param data: file data
        :return: content str, metadata dict
        """
        meta = {}
        try:
            idx = data.index(END_OF_TEXT)
            content = data[:idx]
            lines = data[idx:].splitlines()
        except ValueError:
            # idx not found
            content = data
            lines = []

        for line in lines:
            try:
                key, value = line.strip().split(':', 1)
                if key == 'tags':
                    tags = re.findall(r'\w+', value)  # find all words
                    meta['tags'] = ' '.join(tags)
                else:
                    meta[key] = value
            except ValueError:
                pass
        return content, meta