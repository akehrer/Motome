#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_motome_notemodel
----------------------------------

Tests for `Motome.Modules.NoteModel`
"""

import glob
import os
import shutil
import unittest

from Motome.Modules.NoteModel import NoteModel
from Motome.config import NOTE_EXTENSION, HISTORY_FOLDER, END_OF_TEXT

TESTS_DIR = os.path.join(os.getcwd(), 'tests')
TESTER_NOTES_PATH = os.path.join(os.getcwd(), 'tests', 'notes_for_testing')

ZEN_TEXT_FILE = os.path.join(os.getcwd(), 'tests', 'zen.txt')


class TestNoteModel(unittest.TestCase):

    def setUp(self):
        self.notepaths = set(glob.glob(TESTER_NOTES_PATH + '/*' + NOTE_EXTENSION))
        self.db_notes = dict()
        for filepath in self.notepaths:
            filename = os.path.basename(filepath)
            if filename not in self.db_notes.keys():
                note = NoteModel(filepath)
                self.db_notes[note.filename] = note

    def test_add_remove(self):
        filepath = os.path.join(TESTER_NOTES_PATH, 'zen' + NOTE_EXTENSION)
        zen_note = NoteModel(filepath)

        # file doesn't exist yet
        self.assertFalse(os.path.exists(filepath))
        self.assertEqual(zen_note.content, '')
        self.assertEqual(zen_note.timestamp, -1)
        self.assertEqual(zen_note.metadata, dict())
        self.assertEqual(zen_note.history, list())
        self.assertEqual(zen_note.wordset, '')
        self.assertFalse(zen_note.recorded)
        self.assertFalse(zen_note.pinned)

        # add content
        content = NoteModel.enc_read(ZEN_TEXT_FILE)
        zen_note.content = content
        self.assertTrue(os.path.exists(filepath))
        self.assertNotEqual(zen_note.metadata, dict())
        self.assertNotEqual(zen_note.timestamp, -1)

        # remove note
        zen_note.remove()
        self.assertFalse(os.path.exists(filepath))
        self.assertEqual(zen_note.content, '')
        self.assertEqual(zen_note.timestamp, -1)
        self.assertEqual(zen_note.metadata, dict())
        self.assertEqual(zen_note.history, list())
        self.assertEqual(zen_note.wordset, '')
        self.assertFalse(zen_note.recorded)
        self.assertFalse(zen_note.pinned)

    def test_add_rename(self):
        filepath = os.path.join(TESTER_NOTES_PATH, 'zen' + NOTE_EXTENSION)
        zen_note = NoteModel(filepath)

        # add content
        content = NoteModel.enc_read(ZEN_TEXT_FILE)
        zen_note.content = content
        self.assertTrue(os.path.exists(filepath))
        self.assertNotEqual(zen_note.metadata, dict())
        self.assertNotEqual(zen_note.timestamp, -1)

        # rename
        filepath2 = os.path.join(TESTER_NOTES_PATH, 'zen2' + NOTE_EXTENSION)
        zen_note.notename = 'zen2'
        self.assertTrue(os.path.exists(filepath2))
        self.assertEqual(zen_note.notename, 'zen2')

    def test_add_record(self):
        filepath = os.path.join(TESTER_NOTES_PATH, 'zen' + NOTE_EXTENSION)
        zen_note = NoteModel(filepath)

        # add content
        content = NoteModel.enc_read(ZEN_TEXT_FILE)
        zen_note.content = content

        # record
        self.assertFalse(os.path.exists(zen_note.historypath))
        self.assertEqual(zen_note.load_old_note(0), (None, None))
        zen_note.record(TESTER_NOTES_PATH)
        self.assertTrue(os.path.exists(zen_note.historypath))
        self.assertNotEqual(zen_note.history, list())
        self.assertNotEqual(zen_note.load_old_note(0), (None, None))

    def test_get_changed_content(self):
        notename = self.db_notes.keys()[0]
        note = self.db_notes[notename]
        filepath = note.filepath

        # Read data from file, not using NoteModel
        raw_data = NoteModel.enc_read(filepath)
        content, metadata = NoteModel.parse_note_content(raw_data)
        timestamp = os.stat(filepath).st_mtime

        self.assertEqual(note.content, content)
        self.assertEqual(note.timestamp, timestamp)

        # Make a change
        new_content = content + '\nNew line\n'
        self.assertNotEqual(note.content, new_content)

        # Write changed data not from NoteModel
        filedata = new_content + END_OF_TEXT + '\n'
        for key, value in metadata.items():
            filedata = filedata + '{0}:{1}\n'.format(key, value)
        NoteModel.enc_write(filepath, filedata)

        # Change happened?
        self.assertNotEqual(note.timestamp, timestamp)

        # And the content automatically updates when accessed
        self.assertEqual(note.content, new_content)

        # Reset file
        filedata = content + END_OF_TEXT + '\n'
        for key, value in metadata.items():
            filedata = filedata + '{0}:{1}\n'.format(key, value)
        NoteModel.enc_write(filepath, filedata)

    def tearDown(self):
        # Clear out any vestiges of the zen files
        zenpaths = glob.glob(TESTER_NOTES_PATH + '/zen*' + NOTE_EXTENSION)
        for zen in zenpaths:
            os.remove(zen)
        # Remove the archive folder
        if os.path.exists(os.path.join(TESTER_NOTES_PATH, HISTORY_FOLDER)):
            shutil.rmtree(os.path.join(TESTER_NOTES_PATH, HISTORY_FOLDER))


if __name__ == '__main__':
    unittest.main()