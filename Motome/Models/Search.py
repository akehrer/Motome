# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Import configuration values
from Motome.config import TAG_QUERY_CHAR


class SearchModel(object):
    def __init__(self):
        self._query = ''

        self.ignore_items = []
        self.use_words = []
        self.use_tags = []
        self.ignore_tags = []
        self.ignore_words = []

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
        self.use_words = [x for x in search_terms if x[0] != '-' and x[0] != TAG_QUERY_CHAR]
        self.use_tags = [t[1:] for t in search_terms if t[0] == TAG_QUERY_CHAR]
        self.ignore_tags = [t[1:] for t in self.ignore_items if len(t) > 2 and t[0] == TAG_QUERY_CHAR]
        self.ignore_words = [t for t in self.ignore_items if len(t) > 2 and t[0] != TAG_QUERY_CHAR]

    def search_notemodel(self, note_model):
        content_words = note_model.wordset
        try:
            content_tags = note_model.metadata['tags']
        except (KeyError, TypeError):
            content_tags = ''

        has_tag_filters = len(self.use_tags + self.ignore_tags) > 0  # are there tags in the search term
        has_word_filters = len(self.use_words + self.ignore_words) > 0  # are there words in the search term

        yay_tags = all([tag in content_tags for tag in self.use_tags]) if has_tag_filters else True
        boo_tags = all([tag not in content_tags for tag in self.ignore_tags]) if has_tag_filters else True
        yay_words = all([word in content_words for word in self.use_words]) if has_word_filters else True
        boo_words = all([word not in content_words for word in self.ignore_words]) if has_word_filters else True

        return all([yay_words, boo_words, yay_tags, boo_tags])