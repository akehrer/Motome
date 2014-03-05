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

import yaml

from Motome.config import ZIP_EXTENSION, NOTE_EXTENSION, ENCODING, STATUS_TEMPLATE, HISTORY_FOLDER, YAML_BRACKET

# Set up the logger
logger = logging.getLogger(__name__)


class NoteModel(object):
    """
    The main note model contains note information and name conversions for a given note.
    It also handles reading and writing data to the note file.
    """
    def __init__(self, filepath=None):
        self.filepath = filepath
        self.wordset = ''
        self.is_saved = True

        self._content = ''
        self._metadata = {}
        self._history = []
        self._last_seen = -1

    def __repr__(self):
        return '<Note: {0}, Last Modified: {1}>'.format(self.notename, self.timestamp)

    def __getstate__(self):
        """ This is used when pickling to remove data we don't want to store
        """
        state = self.__dict__.copy()
        state['_content'] = ''
        state['_history'] = []
        state['is_saved'] = True
        return state

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.filepath == other.filepath

    @property
    def content(self):
        if self.timestamp > self._last_seen or self._content == '':
            self._update_from_file()
        return self._content

    @content.setter
    def content(self, value):
        if value != self._content:
            self._content = value
            self.is_saved = False
            # self._save_to_file()

    @property
    def metadata(self):
        if self.timestamp > self._last_seen:
            self._update_from_file()
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """ The note's metadata setter, expects a dict

        :param value: dict of the new metadata
        """
        self._metadata = value
        self.is_saved = False
        # self._save_to_file()

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
        except (KeyError, TypeError):
            return False

    @pinned.setter
    def pinned(self, value):
        if value:
            self._metadata['pinned'] = 1
        else:
            self._metadata['pinned'] = 0
        self.is_saved = False
        # self.save_to_file()

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
        """ Handles renaming the note so makes sure all the files get renamed too

        :param value: string of the new name
        """
        basepath, ext = os.path.splitext(self.filepath)
        newname = value + ext
        newpath = ''.join([basepath[:-len(self.notename)], newname])
        try:
            shutil.move(self.filepath, newpath)
        except OSError:
            logging.error('Note renaming error: %s to %s'%(self.notename, value))
            return
        try:
            new_history = os.path.join(self.notedirectory, HISTORY_FOLDER, newname) + ZIP_EXTENSION
            shutil.move(self.historypath, new_history)
        except IOError:
            pass
        self.filepath = newpath

    @property
    def historypath(self):
        return os.path.join(self.notedirectory, HISTORY_FOLDER, self.filename) + ZIP_EXTENSION

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
    def hashname(self):
        try:
            return hashlib.sha1(self.filepath.encode('UTF-8')).hexdigest()
        except AttributeError:
            return None

    @property
    def timestamp(self):
        try:
            return os.stat(self.filepath).st_mtime
        except OSError:
            return -1

    @property
    def title(self):
        if 'title' in self.metadata.keys():
            return self.metadata['title']
        else:
            return self.unsafename

    @property
    def urls(self):
        """ Get all the urls from the content

        :return: a list of (title, url) tuples found in the content
        """
        url_re_compile = re.compile(r'\[([^\[]+)\]\(([^\)]+)\)', re.VERBOSE | re.MULTILINE)
        return url_re_compile.findall(self.content)

    def load_old_note(self, index):
        """ Load a note from the history

        :param index: the index value in the history list
        :returns: a tuple containing the unparsed note content, a date string ('YYYYMMDDHHMMSS')
        """
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

    def record(self):
        """ Write the old file data to the zip archive
        """
        history_dir = os.path.join(self.notedirectory, HISTORY_FOLDER)
        now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        old_filename = now + NOTE_EXTENSION
        old_filepath = os.path.join(history_dir, old_filename)
        
        # create the history storage directory
        if not os.path.exists(history_dir):
            try:
                os.makedirs(history_dir)
            except OSError as e:
                logger.warning(e)
                return

        self.save_to_file()
        self.save_to_file(filepath=old_filepath)

        zip_filepath = self.historypath  # self.filepath + ZIP_EXTENSION
        with zipfile.ZipFile(zip_filepath, 'a') as myzip:
            myzip.write(old_filepath, old_filename)
        os.remove(old_filepath)

    def rename(self):
        """ Renames the note using the metadata['title'] value
        """
        if self._metadata['title'] == self.notename:
            return
        else:
            self.notename = self._metadata['title']
        return self

    def remove(self):
        """ Deletes all the note's associated files and clears the object's properties

        :return: boolean of removal success
        """
        ret = False
        paths = [self.filepath,
                 self.historypath]
        for path in paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    ret = True
                except OSError as e:
                    logger.warning(e)
        if ret:
            # clear all info
            self.wordset = ''
            self._content = ''
            self._metadata = {}
            self._history = []
            self._last_seen = -1
        return ret

    def get_status(self):
        """ Create an html document of basic note status information

        :return: an html document of note status data
        """
        dt = datetime.datetime.fromtimestamp(self.timestamp)
        html = STATUS_TEMPLATE.format(notename=self.notename,
                                      timestamp=dt.strftime('%c'),
                                      recorded=self._latest_record_date())
        return html

    def _latest_record_date(self):
        """ Get a string of the last history record's datetime

        :return: A string representation of the date and time
        """
        try:
            dt = self.history[-1].date_time
            latest_dt = datetime.datetime(*dt)
            return latest_dt.strftime('%c')
        except IndexError:
            return 'Never'

    def _update_from_file(self):
        """ Update the object's internal values from the file
        """
        try:
            self._content, self._metadata = self.parse_note_content(self.enc_read(self.filepath))
            self._last_seen = self.timestamp
            self.wordset = ' '.join(set(re.findall(r'\w+', self._content.lower())))
        except IOError:
            # file not there or couldn't access it, things may be different
            self._last_seen = -1

    def save_to_file(self, filepath=None):
        """ Save the content and metadata to the note file
        """
        if filepath is None:
            filepath = self.filepath
        if not 'title' in self.metadata.keys():
            self.metadata['title'] = self.notename
        if self.content[-1] == '\n':
            filedata = self.content
        else:
            filedata = self.content + '\n'
        # use safe_dump to prevent dumping non-standard YAML tags
        filedata += YAML_BRACKET + '\n' + yaml.safe_dump(self.metadata, default_flow_style=False) + YAML_BRACKET
        self.enc_write(filepath, filedata)
        self.is_saved = True

    @staticmethod
    def safe_filename(filename):
        """ Convert the filename into something more url safe

        :param filename:
        :return: safer filename string or None on failure
        """
        # TODO: Look at a slugify module instead
        pattern = re.compile('[\W_]+')  # find all words
        root, ext = os.path.splitext(os.path.basename(filename))
        return pattern.sub('_', root) if ext is '' else ''.join([pattern.sub('_', root), ext])

    @staticmethod
    def parse_note_content(data):
        """ Given a file's raw data, split it into its note content and metadata.

        :param data: file data
        :return: content str, metadata dict
        """
        meta = dict()
        try:
            # find the metadata at the end of the document
            s = data.split(YAML_BRACKET)
            m = s[-2]
            content = ''.join(s[:-2])
            meta = yaml.safe_load(m.strip())  # use safe_load to prevent loading non-standard YAML tags
        except IndexError:
            content = data
        except yaml.YAMLError:
            content = data
        return content, meta

    @staticmethod
    def enc_write(filepath, filedata):
        """ Encode and write data to a file (unicode inside, bytes outside)

        :param filepath: the path to the output file
        :param filedata: the data to write
        """
        # encode things
        ufilepath = filepath.encode(ENCODING)
        ufiledata = filedata.encode(ENCODING)
        with open(ufilepath, mode='wb') as f:
            f.write(ufiledata)

    @staticmethod
    def enc_read(filepath):
        """ Read and decode data from a file (bytes outside, unicode inside)

        :param filepath: the path to the input file
        :return: decoded file data
        """
        ufilepath = filepath.encode(ENCODING)
        with open(ufilepath, mode='rb') as f:
            data = f.read()
        return data.decode(ENCODING)