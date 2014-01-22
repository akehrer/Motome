# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Import standard library modules
import cPickle as pickle
import glob
import gzip
import os
import re
from collections import Counter
from itertools import tee, islice, imap

# Import utilities
from Motome.Modules.Utils import open_and_parse_note, safe_filename

# Import configuration values
from Motome.config import NOTE_EXTENSION, INDEX_EXTENSION, TAG_QUERY_CHAR, LOCK_EXTENSION, NOTE_DATA_DIR


class SearchModel(object):
    def __init__(self):
        self._query = ''

        self.ignore_items = []
        self.use_items = []
        self.use_tags = []
        self.ignore_tags = []

    @property
    def query(self):
        return self._query

    @query.setter
    def query(self, value):
        self._query = value
        self.parse_query()

    def parse_query(self):
        search_terms = self.query.split()
        self.ignore_items = [t[1:] for t in search_terms if t[0] == '-']
        self.use_items = [x for x in search_terms if x[0] != '-' and x[0] != TAG_QUERY_CHAR]
        self.use_tags = [t[1:] for t in search_terms if t[0] == TAG_QUERY_CHAR]
        self.ignore_tags = [t[1:] for t in self.ignore_items if len(t) > 2 and t[0] == TAG_QUERY_CHAR]

    def search_notemodel(self, note_model):
        content_words = note_model.wordset
        good_tags = len([tag for tag in self.use_tags if tag in note_model.metadata['tags']]) > 0
        no_bad_tags = len([tag for tag in self.ignore_tags if tag in note_model.metadata['tags']]) == 0
        good_words = all([word in content_words for word in self.use_items])
        no_bad_words = len([word for word in self.ignore_items if word in content_words]) == 0
        
        if good_tags and no_bad_tags:
            return good_words
        elif len(self.use_tags) == 0:
            return good_words and (no_bad_words and no_bad_tags)
        else:
            return False
        # return (good_tags or (good_words and words_in_set)) and (bad_words and bad_tags)

class SearchNotes(object):
    """
    A class for index creation and search of note documents
    """
    def __init__(self, notes_dir, note_extension=NOTE_EXTENSION):
        self.notes_dir = notes_dir
        self.note_extension = note_extension
        self.index_dir = os.path.join(self.notes_dir, NOTE_DATA_DIR)

        # create the index storage directory
        try:
            os.makedirs(self.index_dir)
            self.first_run = True
        except OSError:
            self.first_run = False

        self.notes_list = []

        if os.path.exists(self.notes_dir):
            #self._clean_locks()
            self._get_notes_list()
        else:
            raise SearchLocationError(self.notes_dir)

    def __repr__(self):
        return '<SearchNotes: {0}>'.format(self.notes_dir)

    def add(self, filepath):
        self.notes_list.append(filepath)
        self._build_file_index(filepath)

    def update(self, filepath):
        self._build_file_index(filepath)

    def remove(self, filepath):
        try:
            safename = safe_filename(os.path.basename(filepath))
            index_filepath = os.path.join(self.index_dir, safename) + INDEX_EXTENSION
            os.remove(index_filepath)
        except OSError:
            # file not there?
            pass
        finally:
            self._get_notes_list()

    def run(self, q):
        """
        Run query against the index files and return a list of SearchResults.
        """
        results = []
        query = SearchQuery(q)
        query.words, query.collection = self._build_collection(q)
        for notepath in self.notes_list:
            index = self._load_file_index(notepath)
            r = SearchResult(notepath, index, query)
            if r.matchsum > 0:
                results.append(r)
        return results

    def build_index(self):
        """
        (Re)build the search index
        """
        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)

        for notepath in self.notes_list:
            self.update(notepath)

    def _get_notes_list(self):
        self.notes_list = glob.glob(self.notes_dir + '/*' + NOTE_EXTENSION)

    def _build_file_index(self, notepath, commit=True):
        content, metadata = open_and_parse_note(notepath)
        if not 'tags' in metadata.keys():
            metadata['tags'] = ''
        if not 'title' in metadata.keys():
            metadata['title'] = ''

        words, collection = self._build_collection(content)

        index = SearchIndex(metadata['title'])
        index.tags = metadata['tags']
        index.words = words
        index.collection = collection

        if commit:
            self._lock_index(notepath)
            safename = safe_filename(os.path.basename(notepath))
            index_filepath = os.path.join(self.index_dir, safename) + INDEX_EXTENSION
            with gzip.GzipFile(index_filepath, 'wb') as myzip:
                pickle.dump(index, myzip, pickle.HIGHEST_PROTOCOL)
            self._unlock_index(notepath)

    def _load_file_index(self, notepath):
        safename = safe_filename(os.path.basename(notepath))
        index_filepath = os.path.join(self.index_dir, safename) + INDEX_EXTENSION
        try:
            with gzip.GzipFile(index_filepath, 'rb') as myzip:
                index = pickle.load(myzip)
            return index
        except IOError:
            raise SearchError

    def _build_collection(self, content):
        """
        Taking a string of text return a set of unique words and a Counter collection of word bigrams.
        """
        try:
            words = re.findall("\w+", content.lower())
            collection = Counter(self._generate_ngrams(words, 2))
            return set(words), collection
        except AttributeError:
            # empty string sent
            return set(), Counter()

    def _generate_ngrams(self, words, n):
        """
        http://stackoverflow.com/questions/12488722/counting-bigrams-pair-of-two-words-in-a-file-using-python
        """
        tlst = words
        while True:
            a, b = tee(tlst)
            l = tuple(islice(a, n))
            if len(l) == n:
                yield l
                next(b)
                tlst = b
            else:
                break

    def _lock_index(self, notepath):
        """
        Lock an index file to prevent access
        """
        safename = safe_filename(os.path.basename(notepath))
        lock_filepath = os.path.join(self.index_dir, safename) + LOCK_EXTENSION
        with open(lock_filepath, 'w') as fp:
            pid = os.getpid()
            fp.write('pid:{0}\n'.format(pid))

    def _unlock_index(self, notepath):
        safename = safe_filename(os.path.basename(notepath))
        lock_filepath = os.path.join(self.index_dir, safename) + LOCK_EXTENSION
        os.remove(lock_filepath)

    def _clean_locks(self):
        current_pid = os.getpid()
        for filename in os.listdir(self.index_dir):
            if filename.endswith(LOCK_EXTENSION):
                path = os.path.join(self.index_dir, filename)
                data = {}
                with open(path, 'r') as fp:
                    for line in fp.readlines():
                        key, val = line.split(':')
                        data[key] = val
                if 'pid' in data.keys():
                    if data['pid'] != current_pid:
                        os.remove(os.path.join(self.index_dir, filename))


class SearchIndex(object):
    """
    The search index items for a note.
    words is a set of the document's unique words
    collection is a collection.Counter object of the document's ngrams
    """
    def __init__(self, title):
        self.title = title
        self.tags = None
        self.words = None
        self.collection = None

    def __repr__(self):
        return '<SearchIndex: {0}}>'.format(self.title)


class SearchQuery(object):
    """
    The search query items.
    words is a set of the query's unique words
    collection is a collection.Counter object of the query's ngrams
    """
    def __init__(self, query):
        self.query = query
        self.words = None
        self.collection = None

    @property
    def tags(self):
        try:
            return [t[1:] for t in self.query.split() if t[0] == TAG_QUERY_CHAR]
        except AttributeError:
            # no tags in query
            return None

    def __repr__(self):
        return '<SearchQuery: {0}>'.format(self.query)


class SearchResult(object):
    """
    The search result items for a specific note.
    """
    def __init__(self, notepath, index, query):
        self.filepath = notepath
        self.index = index
        self.query = query

        self.wordmatch = list(query.words & index.words)
        self.ngrammatch = query.collection & index.collection

    @property
    def matchsum(self):
        try:
            return sum(imap(len, [self.tagmatch, self.wordmatch, self.ngrammatch]))
        except TypeError:
            return 0

    @property
    def tagmatch(self):
        try:
            return [t for t in self.query.tags if t in self.index.tags]
        except TypeError:
            return []

    def __repr__(self):
        return '<SearchResult: {0}, Matchsum: {1}>'.format(self.filepath, self.matchsum)


class SearchError(Exception):
    """Base class for SearchNotes errors."""
    pass


class SearchLocationError(SearchError):
    """SearchNote location doesn't exist"""
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return '<SearchLocationError: {0} not found!'.format(self.path)