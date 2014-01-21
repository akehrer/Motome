# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import datetime
import hashlib
import logging
import os
import re
import shutil
import zipfile

from Motome.config import END_OF_TEXT, ZIP_EXTENSION, NOTE_EXTENSION, ENCODING, STATUS_TEMPLATE, HISTORY_FOLDER

# Set up the logger
logger = logging.getLogger(__name__)


class NoteModel(object):
    """
    The main note model contains the note information and name conversions for a given note.
    """
    def __init__(self, filepath=None):
        self.filepath = filepath
        self.wordset = set()

        self._content = ''
        self._metadata = {}
        self._history = []
        self._last_seen = 0

    def __repr__(self):
        return '<Note: {0}, Last Modified: {1}>'.format(self.notename, self.timestamp)

    def __getstate__(self):
        state = self.__dict__.copy()
        state['_content'] = ''
        return state

    @property
    def content(self):
        if self.timestamp > self._last_seen or self._content == '':
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
        self._metadata = value
        self._save_to_file()

    @property
    def history(self):
        zip_filepath = self.historypath
        self._history = []
        try:
            with zipfile.ZipFile(zip_filepath, 'r') as myzip:
                self._history = sorted(myzip.infolist(), key=lambda x: x.filename)
        except IOError:
            pass
        return self._history

    @property
    def pinned(self):
        try:
            if int(self.metadata['pinned']) > 0:
                return True
            else:
                return False
        except KeyError:
            return False

    @pinned.setter
    def pinned(self, value):
        if value:
            self._metadata['pinned'] = 1
        else:
            self._metadata['pinned'] = 0
        self._save_to_file()

    @property
    def recorded(self):
        if len(self.history) == 0:
            return False
        else:
            two_sec = datetime.timedelta(seconds=2)
            dt = self.history[-1].date_time
            latest_dt = datetime.datetime(*dt)
            current_dt = datetime.datetime.fromtimestamp(self.timestamp)
            if abs(current_dt - latest_dt) < two_sec:
                return True
            else:
                return False

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

    @notename.setter
    def notename(self, value):
        basepath, ext = os.path.splitext(self.filepath)
        newpath = basepath[:-len(self.notename)] + value + ext
        try:
            shutil.move(self.filepath, newpath)
        except OSError:
            logging.error('Note renaming error: %s to %s'%(self.notename, value))
            return
        try:
            shutil.move(self.historypath, newpath + ZIP_EXTENSION)
        except IOError:
            pass
        self.filepath = newpath

    @property
    def historypath(self):
        return os.path.join(self.notedirectory, HISTORY_FOLDER, self.filename) + ZIP_EXTENSION # self.filepath + ZIP_EXTENSION

    @property
    def notedirectory(self):
        return os.path.dirname(self.filepath)

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
            return 0.0

    def load_old_note(self, index):
        try:
            zip_filepath = self.historypath
            with zipfile.ZipFile(zip_filepath, 'r') as myzip:
                old_content_bytes = myzip.read(self.history[index])
                old_content = old_content_bytes.decode(ENCODING)
                old_date = self.history[index].filename[:-(len(ZIP_EXTENSION)+1)]
        except Exception as e:
            logger.debug('[NoteModel/load_old_note] %s'%e)
            old_content = None
            old_date = None
        return old_content, old_date

    def record(self, notes_dir):
        """
        Write the old file data to the zip archive

        :param notes_dir:
        """
        history_dir = os.path.join(notes_dir, HISTORY_FOLDER)
        now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        old_filename = now + NOTE_EXTENSION
        old_filepath = os.path.join(history_dir, old_filename)

        self._save_to_file()
        self._save_to_file(filepath=old_filepath)

        zip_filepath = self.historypath  # self.filepath + ZIP_EXTENSION
        with zipfile.ZipFile(zip_filepath, 'a') as myzip:
            myzip.write(old_filepath, old_filename)
        os.remove(old_filepath)

    def rename(self):
        if self._metadata['title'] == self.notename:
            return
        else:
            self.notename = self._metadata['title']

    def get_status(self):
        dt = datetime.datetime.fromtimestamp(self.timestamp)
        html = STATUS_TEMPLATE.format(notename=self.notename,
                                      timestamp=dt.strftime('%c'),
                                      recorded=self._latest_record_date())
        return html

    def _latest_record_date(self):
        try:
            dt = self.history[-1].date_time
            latest_dt = datetime.datetime(*dt)
            return latest_dt.strftime('%c')
        except IndexError:
            return 'Never'

    def _update_from_file(self):
        self._content, self._metadata = self.parse_note_content(self.enc_read(self.filepath))
        self._last_seen = self.timestamp
        self.wordset = set(re.findall(r'\w+', self._content.lower()))

    def _save_to_file(self, filepath=None):
        """
        Save the content and metadata to the note file
        """
        if filepath is None:
            filepath = self.filepath
        if not 'title' in self.metadata.keys():
            self.metadata['title'] = self.notename
        filedata = self.content + '\n' + END_OF_TEXT + '\n'
        for key, value in self.metadata.items():
                filedata = filedata + '{0}:{1}\n'.format(key, value)
        self.enc_write(filepath, filedata)

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

    @staticmethod
    def enc_write(filepath, filedata):
        # encode things
        ufilepath = filepath.encode(ENCODING)
        ufiledata = filedata.encode(ENCODING)
        with open(ufilepath, mode='wb') as f:
            f.write(ufiledata)

    @staticmethod
    def enc_read(filepath):
        ufilepath = filepath.encode(ENCODING)
        with open(ufilepath, mode='rb') as f:
            data = f.read()
        return data.decode(ENCODING)