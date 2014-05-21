# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Import standard library modules
import logging
import os
import shutil
import sys
import time
import cPickle as pickle
import yaml
from datetime import datetime

# Import extra modules
import markdown

# Import Qt modules
from PySide import QtCore, QtGui

# Import application window view
from Motome.Controllers.SettingsDialog import SettingsDialog
from Motome.Views.MainWindow import Ui_MainWindow

# Import configuration values
from Motome.config import NOTE_EXTENSION, MEDIA_FOLDER, APP_DIR, WINDOW_TITLE, VERSION, \
    NOTE_DATA_DIR, HTML_FOLDER, HTML_EXTENSION, MOTOME_BLUE, DEFAULT_NOTES_DIR

# Import additional modules
from Motome.Models.NoteModel import NoteModel
from Motome.Models.NoteListWidget import NoteListWidget
from Motome.Models.MotomeTextBrowser import MotomeTextBrowser
from Motome.Models.AutoCompleterModel import AutoCompleteEdit
from Motome.Models.Search import SearchModel
from Motome.Models.Utils import build_preview_footer_html, build_preview_header_html, \
    diff_to_html, human_date, pickle_find_NoteModel, history_timestring_to_datetime, clean_filename

# Set up the logger
logger = logging.getLogger(__name__)


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None, portable=False):
        super(MainWindow, self).__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle(WINDOW_TITLE)

        self.portable_mode = portable  # the portable mode flag is set by the command line argument 'portable'

        # create the app configuration storage directory
        if self.portable_mode:
            self.user_home_dir = APP_DIR
        else:
            self.user_home_dir = os.path.expanduser('~')
        self.app_data_dir = os.path.join(self.user_home_dir, '.Motome')

        try:
            os.makedirs(self.app_data_dir)
            self.first_run = True
        except OSError:
            self.first_run = False

        # current notes directory session data file location
        self.notes_dir = ''
        self.notes_data_dir = ''

        # Configuration and defaults
        self.conf = {}
        self.record_on_save = False
        self.record_on_exit = False
        self.record_on_switch = False
        self.first_line_title = True

        # notes list splitter size for hiding and showing the notes list
        self.notes_list_splitter_size = None

        # Load configuration
        self.load_conf()
        self.set_config_vars()

        # session notes dict
        self.session_notes_dict = {}

        # revision note content
        self.old_data = None

        # markdown translator
        self.md = markdown.Markdown()

        # save metadata timer
        self.save_meta_interval = 1000  # msec
        self.save_meta_timer = QtCore.QTimer()
        self.save_meta_timer.timeout.connect(self.save_note_meta)

        # save unsaved timer
        self.save_interval = 5 * 1000  # msec
        self.save_timer = QtCore.QTimer()
        self.save_timer.timeout.connect(self.save_the_unsaved)
        self.save_timer.start(self.save_interval)

        # search
        self.search = SearchModel()
        self.query = ''
        self.search_interval = 250  # msec
        self.search_timer = QtCore.QTimer()
        self.search_timer.timeout.connect(self.search_notes)

        # custom window elements
        self.notesList = None
        self.noteEditor = None
        self.tagEditor = None
        self.notesLocationsList = None

        # setup GUI elements
        self.keyboard_shortcuts = {}
        self.setting_button_icons = {}
        self.setup_keyboard_shortcuts()
        self.setup_settings_button_icons()
        self.setup_mainwindow()
        self.setup_preview()
        self.setup_diff()
        self.setup_history()
        self.insert_ui_noteslist()
        self.insert_ui_noteeditor()
        self.insert_ui_tageditor()
        self.insert_ui_notesLocationsList()

        # load the text browser styles
        self.style_dir = os.path.join(APP_DIR, 'styles', 'default')
        self.load_styles()

        if self.first_run:
            logger.info('First run')
            self.do_first_run()
        else:
            self.load_session_data()
            self.noteEditor.session_notemodel_dict = self.session_notes_dict
            self.notesList.notes_dir = self.notes_dir

        # set the focus to the window frame
        self.setFocus(QtCore.Qt.ActiveWindowFocusReason)

    @property
    def current_note(self):
        try:
            return self.notesList.currentItem().notemodel
        except AttributeError:
            return None

    def stop(self):
        if self.noteEditor.save_timer.isActive():
            self.noteEditor.save_note()

        if self.save_meta_timer.isActive():
            self.save_note_meta()

        self.save_the_unsaved()
        self.save_timer.stop()

        if self.record_on_exit:
            unrecorded = (nw.notemodel for nw in self.notesList.all_items if not nw.notemodel.recorded)
            for note in unrecorded:
                note.record()

        self.save_session_data()

        # set the current notes directory to be the default next time
        self.conf['conf_notesLocation'] = self.notes_dir

        # save the window position and geometry
        window_geo = self.geometry()
        self.conf['window_x'] = window_geo.x()
        self.conf['window_y'] = window_geo.y()
        self.conf['window_width'] = window_geo.width()
        self.conf['window_height'] = window_geo.height()
        self.save_conf()

    def do_first_run(self):
        """ Do stuff the first time the app runs """
        # Show them the settings dialog
        self.load_settings()
        self.load_session_data()
        self.first_run = False

    def setup_mainwindow(self):
        # load main window style
        main_style_path = os.path.join(APP_DIR, 'styles', 'main_window.css')
        main_style = NoteModel.enc_read(main_style_path)
        self.setStyleSheet(main_style)

    def setup_preview(self):
        # catch link clicks in the Preview pane
        self.ui.notePreview.setOpenExternalLinks(True)
        self.ui.notePreview.anchorClicked.connect(self.load_anchor)
        self.ui.notePreview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.notePreview.customContextMenuRequested.connect(self.show_custom_preview_menu)
        self.ui.notePreview.setSearchPaths(self.notes_dir)

    def setup_diff(self):
        self.ui.noteDiff.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.noteDiff.customContextMenuRequested.connect(self.show_custom_diff_menu)

    def setup_history(self):
        self.ui.frameHistory.hide()

    def setup_keyboard_shortcuts(self):
        """ Setup the keyboard shortcuts and load the keyboard_shortcuts dict for use elsewhere
        """
        esc = QtCore.Qt.Key_Escape
        delete = QtCore.Qt.Key_Delete
        self.keyboard_shortcuts = {'New': {'seq': QtGui.QKeySequence('Ctrl+N'),
                                           'func': lambda item=None: self.process_keyseq('ctrl_n')},
                                   'Find': {'seq': QtGui.QKeySequence('Ctrl+F'),
                                            'func': lambda item=None: self.process_keyseq('ctrl_f')},
                                   'ShowEdit': {'seq': QtGui.QKeySequence('Ctrl+E'),
                                                'func': lambda item=None: self.process_keyseq('ctrl_e')},
                                   'ShowPre': {'seq': QtGui.QKeySequence('Ctrl+W'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_w')},
                                   'ShowDiff': {'seq': QtGui.QKeySequence('Ctrl+D'),
                                                'func': lambda item=None: self.process_keyseq('ctrl_d')},
                                   'NoteList': {'seq': QtGui.QKeySequence('Ctrl+L'),
                                                'func': lambda item=None: self.process_keyseq('ctrl_l')},
                                   'TagEdit': {'seq': QtGui.QKeySequence('Ctrl+T'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_t')},
                                   'Save': {'seq': QtGui.QKeySequence('Ctrl+S'),
                                            'func': lambda item=None: self.process_keyseq('ctrl_s')},
                                   'Record': {'seq': QtGui.QKeySequence('Ctrl+R'),
                                              'func': lambda item=None: self.process_keyseq('ctrl_r')},
                                   'Print': {'seq': QtGui.QKeySequence('Ctrl+P'),
                                             'func': lambda item=None: self.process_keyseq('ctrl_p')},
                                   'UpNote': {'seq': QtGui.QKeySequence('Ctrl+]'),
                                              'func': lambda item=None: self.process_keyseq('ctrl_up')},
                                   'DownNote': {'seq': QtGui.QKeySequence('Ctrl+['),
                                                'func': lambda item=None: self.process_keyseq('ctrl_down')},
                                   'BackHist': {'seq': QtGui.QKeySequence('Ctrl+<'),
                                                'func': lambda item=None: self.process_keyseq('ctrl_<')},
                                   'FwdHist': {'seq': QtGui.QKeySequence('Ctrl+>'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_>')},
                                   'TglList': {'seq': QtGui.QKeySequence('Ctrl+Shift+L'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_l')},
                                   'TglHist': {'seq': QtGui.QKeySequence('Ctrl+Shift+H'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_h')},
                                   'TglOmni': {'seq': QtGui.QKeySequence('Ctrl+Shift+O'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_o')},
                                   'TglFull': {'seq': QtGui.QKeySequence('Ctrl+Shift+F'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_f')},
                                   'InsDate': {'seq': QtGui.QKeySequence('Ctrl+Shift+U'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_u')},
                                   'PinNote': {'seq': QtGui.QKeySequence('Ctrl+Shift+P'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_p')},
                                   'ClearOmni': {'seq': QtGui.QKeySequence(esc),
                                                 'func': lambda item=None: self.process_keyseq('esc')},
                                   'DelNote': {'seq': QtGui.QKeySequence(delete),
                                               'func': lambda item=None: self.delete_current_note()}
                                    }
        # create all the shortcuts
        for s in self.keyboard_shortcuts.values():
            QtGui.QShortcut(s['seq'], self, s['func'])

    def setup_settings_button_icons(self):
        self.setting_button_icons = {'default': QtGui.QIcon(":/icons/resources/gear_32x32.png"),
                                     'unsaved': QtGui.QIcon(":/icons/resources/gear_fullcenter_32x32.png"),
                                     'warning': QtGui.QIcon(":/icons/resources/gear_warning_32x32.png"),
                                     'error':   QtGui.QIcon(":/icons/resources/gear_error_32x32.png")
        }

    def insert_ui_noteslist(self):
        self.notesList = NoteListWidget(self.session_notes_dict)
        if self.notes_dir != '':
            self.notesList.notes_dir = self.notes_dir
        self.ui.verticalLayout_3.insertWidget(0, self.notesList)
        self.notesList.itemSelectionChanged.connect(self.update_ui_views)

    def insert_ui_noteeditor(self):
        # insert the custom text editor
        self.noteEditor = MotomeTextBrowser(self)
        self.noteEditor.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard | QtCore.Qt.LinksAccessibleByMouse |
                                                QtCore.Qt.TextBrowserInteraction | QtCore.Qt.TextEditable |
                                                QtCore.Qt.TextEditorInteraction | QtCore.Qt.TextSelectableByKeyboard |
                                                QtCore.Qt.TextSelectableByMouse)
        self.noteEditor.setObjectName("noteEditor")
        self.ui.horizontalLayout_3.insertWidget(0, self.noteEditor)
        self.noteEditor.anchorClicked.connect(self.load_anchor)
        self.noteEditor.noteSaved.connect(self.save_note_meta)  # to check for first line title change
        # Custom right-click menu
        self.noteEditor.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.noteEditor.customContextMenuRequested.connect(self.show_custom_editor_menu)

    def insert_ui_tageditor(self):
        # tag completer
        self.tagEditor = AutoCompleteEdit([])
        self.tagEditor.setObjectName("tagEditor")
        self.tagEditor.setFrame(False)
        self.ui.horizontalLayout_2.addWidget(self.tagEditor)
        self.tagEditor.textEdited.connect(self.start_meta_save)

    def insert_ui_tagcompleter(self):
        # build the completer list
        completer_list = set()
        try:
            for note in self.session_notes_dict.values():
                if 'tags' in note.metadata.keys():
                    for t in note.metadata['tags'].split():
                        completer_list.add(t)
            # attach a completer to the tag editor
            qlist = QtGui.QStringListModel(list(completer_list))
            self.tagEditor.setCompleterModel(qlist)
        except AttributeError:
            pass

    def insert_ui_notesLocationsList(self):
        try:
            if len(self.conf['conf_notesLocations']) > 1:
                self.notesLocationsList = QtGui.QComboBox(self.ui.layoutWidget)
                self.notesLocationsList.setFrame(True)
                self.notesLocationsList.setObjectName("notesLocationsList")
                self.ui.verticalLayout_3.insertWidget(0, self.notesLocationsList)
                self.notesLocationsList.addItems(sorted(self.conf['conf_notesLocations'].values()))
                if self.notes_dir != '':
                    idx = self.notesLocationsList.findText(self.conf['conf_notesLocations'][self.notes_dir])
                    if idx != -1:
                        self.notesLocationsList.setCurrentIndex(idx)
                self.notesLocationsList.currentIndexChanged[str].connect(self.update_notesdir)
            else:
                pass
        except KeyError:
            pass

    def load_session_data(self):
        try:
            with open(os.path.join(self.notes_data_dir, 'Motome_data.fs'), 'rb') as data_file:
                # Practice safer unpickling by making sure the UnPickler only loads NoteModel objects
                unp = pickle.Unpickler(data_file)
                unp.find_global = pickle_find_NoteModel
                self.session_notes_dict = unp.load()
        except IOError:
            self.session_notes_dict = dict()
        except pickle.UnpicklingError as e:
            logger.warning('[load_session_data] %r' % e)

    def save_session_data(self):
        try:
            self.session_notes_dict = self.notesList.session_notemodel_dict
            with open(os.path.join(self.notes_data_dir, 'Motome_data.fs'), 'wb') as data_file:
                pickle.dump(self.session_notes_dict, data_file, -1)
        except IOError:
            os.makedirs(self.notes_data_dir)
            with open(os.path.join(self.notes_data_dir, 'Motome_data.fs'), 'wb') as data_file:
                pickle.dump(self.session_notes_dict, data_file, -1)

    def load_conf(self):
        filepath = os.path.join(self.app_data_dir, 'conf.yml')
        try:
            data = NoteModel.enc_read(filepath)
            try:
                self.conf = yaml.safe_load(data)
            except yaml.YAMLError:
                self.conf = {}

            if not 'conf_notesLocation' in self.conf.keys():
                self.first_run = True
            else:
                self.notes_dir = self.conf['conf_notesLocation']
                self.notes_data_dir = os.path.join(self.notes_dir, NOTE_DATA_DIR)
        except IOError:
            # no conf file
            self.first_run = True

    def save_conf(self):
        filepath = os.path.join(self.app_data_dir, 'conf.yml')
        self.conf['motome_version'] = VERSION
        self.conf['conf_update'] = time.time()
        try:
            data = yaml.safe_dump(self.conf, default_flow_style=False)
            out = '# Motome configuration values\n---\n' + data + '...'
            NoteModel.enc_write(filepath, out)
        except IOError:
            pass

    def set_config_vars(self):
        # Set some configuration variables
        if 'conf_checkbox_recordonsave' in self.conf.keys() and int(self.conf['conf_checkbox_recordonsave']) > 0:
            self.record_on_save = True
        else:
            self.record_on_save = False

        if 'conf_checkbox_recordonexit' in self.conf.keys() and int(self.conf['conf_checkbox_recordonexit']) > 0:
            self.record_on_exit = True
        else:
            self.record_on_exit = False

        if 'conf_checkbox_recordonswitch' in self.conf.keys() and int(self.conf['conf_checkbox_recordonswitch']) > 0:
            self.record_on_switch = True
        else:
            self.record_on_switch = False

        if 'conf_checkbox_firstlinetitle' in self.conf.keys() and int(self.conf['conf_checkbox_firstlinetitle']) > 0:
            self.first_line_title = True
        else:
            self.first_line_title = False

        # Set the window location and size
        if 'window_x' in self.conf.keys() and not self.portable_mode:
            rect = QtCore.QRect(int(self.conf['window_x']),
                                int(self.conf['window_y']),
                                int(self.conf['window_width']),
                                int(self.conf['window_height']))
            self.setGeometry(rect)

    def load_styles(self):
        if 'style' in self.conf.keys():
            self.style_dir = os.path.join(self.app_data_dir, 'styles', self.conf['style'])
        else:
            self.style_dir = os.path.join(APP_DIR, 'styles', 'default')

        editor_path = os.path.join(self.style_dir, 'editor.css')
        preview_path = os.path.join(self.style_dir, 'preview.css')
        diff_path = os.path.join(self.style_dir, 'diff.css')

        if os.path.exists(editor_path):
            editor_style = NoteModel.enc_read(editor_path)
            self.noteEditor.setStyleSheet(editor_style)
            self.noteEditor.document().setDefaultStyleSheet(editor_style)

        if os.path.exists(preview_path):
            preview_style = NoteModel.enc_read(preview_path)
            self.ui.notePreview.document().setDefaultStyleSheet(preview_style)

        if os.path.exists(diff_path):
            diff_style = NoteModel.enc_read(diff_path)
            self.ui.noteDiff.document().setDefaultStyleSheet(diff_style)

    def load_settings(self):
        dialog = SettingsDialog(self.conf)
        dialog.ui.about_version_label.setText('v' + VERSION)
        ret = dialog.exec_()
        if ret:
            # set the current tab to the settings tab
            dialog.ui.tabWidget.setCurrentIndex(0)
            # a tuple of widget types to find in the settings tab
            to_find = (QtGui.QLineEdit, QtGui.QFontComboBox, QtGui.QComboBox, QtGui.QCheckBox)
            # find all the widgets in the settings tab and set the conf dictionary
            for f in to_find:
                for c in dialog.ui.tabWidget.currentWidget().findChildren(f):
                    name = c.objectName()
                    # if name == 'conf_notesLocation':
                    #     self.conf[name] = c.text()
                    if name == 'conf_author':
                        self.conf[name] = c.text()
                    elif name == 'conf_checkbox_recordonsave':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    elif name == 'conf_checkbox_recordonexit':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    elif name == 'conf_checkbox_recordonswitch':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    elif name == 'conf_checkbox_titleasfilename':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    elif name == 'conf_checkbox_firstlinetitle':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    else:
                        pass
            self.save_conf()
            self.set_config_vars()
            # set the notes directories
            try:
                self.conf['conf_notesLocation'] = self.conf['conf_notesLocations'].keys()[0]
                self.notes_dir = self.conf['conf_notesLocation']
                self.notes_data_dir = os.path.join(self.notes_dir, NOTE_DATA_DIR)
                if len(self.conf['conf_notesLocations']) > 1:
                    try:
                        self.update_notesLocationsList()
                    except AttributeError:
                        self.insert_ui_notesLocationsList()
            except KeyError:
                # no notes locations entered during first run
                # create default notes directory
                default_dir = os.path.join(self.user_home_dir, DEFAULT_NOTES_DIR)
                self.conf['conf_notesLocations'] = {default_dir: DEFAULT_NOTES_DIR}
                self.conf['conf_notesLocation'] = default_dir
                self.notes_dir = self.conf['conf_notesLocation']
                self.notes_data_dir = os.path.join(self.notes_dir, NOTE_DATA_DIR)
                try:
                    os.makedirs(default_dir)
                except OSError:
                    pass
                self.show_default_notes_dir_message()

            # get any session data
            self.load_session_data()
            # update the notes list
            self.notesList.session_notemodel_dict = self.session_notes_dict
            self.notesList.notes_dir = self.notes_dir
            # clear the note editor
            self.noteEditor.blockSignals(True)
            self.noteEditor.setHtml('')
            self.noteEditor.blockSignals(False)
            # clear the tag editor
            self.tagEditor.blockSignals(True)
            self.tagEditor.setText('')
            self.tagEditor.blockSignals(False)
        else:
            # user hit cancel
            if not 'conf_notesLocations' in self.conf.keys() or len(self.conf['conf_notesLocations']) == 0:
                sys.exit(1)

    def process_keyseq(self, seq):
        if seq == 'ctrl_n' or seq == 'ctrl_f':
            self.ui.omniBar.setFocus()
        elif seq == 'ctrl_e':
            self.ui.toolBox.setCurrentIndex(0)
            self.noteEditor.setFocus()
        elif seq == 'ctrl_w':
            self.update_ui_preview()
            self.ui.toolBox.setCurrentIndex(1)
        elif seq == 'ctrl_d':
            self.update_ui_diff()
            self.ui.toolBox.setCurrentIndex(2)
        elif seq == 'ctrl_l':
            self.notesList.setFocus()
        elif seq == 'ctrl_t':
            self.ui.toolBox.setCurrentIndex(0)
            self.tagEditor.setFocus()
        elif seq == 'ctrl_s':
            self.noteEditor.save_note()
            self.save_the_unsaved()
            if self.record_on_save:
                self.record_current_note()
        elif seq == 'ctrl_r':
            self.record_current_note()
        elif seq == 'ctrl_p':
            self.print_current_pane()
        elif seq == 'ctrl_up':
            self.keyseq_update_ui_views('down')
        elif seq == 'ctrl_down':
            self.keyseq_update_ui_views('up')
        elif seq == 'ctrl_<':
            self.click_older_date()
        elif seq == 'ctrl_>':
            self.click_newer_date()
        elif seq == 'ctrl_shift_l':
            self.toggle_notes_list_view()
        elif seq == 'ctrl_shift_h':
            self.toggle_history_bar_view()
        elif seq == 'ctrl_shift_o':
            self.toggle_omnibar_view()
        elif seq == 'ctrl_shift_f':
            self.toggle_notes_list_view()
            self.toggle_omnibar_view()
            self.ui.frameHistory.hide()
        elif seq == 'ctrl_shift_u':
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if self.noteEditor.hasFocus():
                self.noteEditor.insertPlainText('{0}\n'.format(now))
            else:
                self.ui.omniBar.setText(now)
        elif seq == 'ctrl_shift_p':
            self.pin_current_note()
        elif seq == 'esc':
            self.ui.omniBar.setText('')
            self.noteEditor.setExtraSelections([])
        else:
            logger.info('No code for {0}'.format(seq))

    def keyseq_update_ui_views(self, direction):
        """
        Moves through the notes list, looping at each end

        :param direction: which direction to move 'up' or 'down'
        """
        what_rownums = [self.notesList.row(i) for i in self.notesList.all_visible_items]
        if len(what_rownums) <= 0:
            return

        current_row = self.notesList.currentRow()
        row_count = self.notesList.count()
        next_row = current_row
        while True:
            if direction == 'down' and next_row > 0:
                next_row -= 1
            elif direction == 'down' and next_row == 0:
                next_row = row_count - 1
            elif direction == 'up' and next_row < row_count - 1:
                next_row += 1
            elif direction == 'up' and next_row == row_count - 1:
                next_row = 0

            if next_row in what_rownums:
                break
        self.notesList.setCurrentRow(next_row)

    def update_notesdir(self, location_val):
        try:
            location_key = [k for k, v in self.conf['conf_notesLocations'].iteritems() if v == location_val][0]
            self.notes_dir = location_key
            self.notesList.notes_dir = location_key
        except IndexError:
            pass

    def update_ui_views(self):
        if self.record_on_switch:
            try:
                if not self.notesList.previous_item.notemodel.recorded:
                    self.notesList.previous_item.notemodel.record()
            except AttributeError:
                pass

        # update the note editor
        self.noteEditor.blockSignals(True)
        self.noteEditor.set_note_text()
        # self.noteEditor.setDocumentTitle(self.current_note.title)  # for things like print to pdf
        self.noteEditor.blockSignals(False)

        # clear any old data
        self.old_data = None

        # highlight any search terms
        if self.query is not '':
            self.noteEditor.highlight_search(self.query.split(' '))

        # update the tag editor
        self.tagEditor.blockSignals(True)
        try:
            self.tagEditor.setText(self.current_note.metadata['tags'])
        except (TypeError, KeyError, AttributeError):
            # no metadata or no tag metadata
            self.tagEditor.setText('')
        self.tagEditor.blockSignals(False)

        # update the preview and diff panes
        self.update_ui_preview()
        self.update_ui_diff()
        self.update_ui_historyLabel()

        # update history information
        self.load_history_data()
        self.update_ui_historyLabel()

        # update the window title
        try:
            title = self.current_note.title
        except AttributeError:
            # current_note is None
            title = ''
        self.setWindowTitle(' '.join([WINDOW_TITLE, '-', title]))

    def update_ui_views_history(self):
        if self.old_data is None:
            self.update_ui_views()
        else:
            old_content, old_meta = NoteModel.parse_note_content(self.old_data[0])
            # update the note editor
            self.noteEditor.blockSignals(True)
            self.noteEditor.set_note_text(old_content)
            self.noteEditor.blockSignals(False)

            # update the tag editor
            self.tagEditor.blockSignals(True)
            try:
                self.tagEditor.setText(old_meta['tags'])
            except (TypeError, KeyError):
                # no metadata or no tag metadata
                self.tagEditor.setText('')
            self.tagEditor.blockSignals(False)

            # update the preview and diff panes
            self.update_ui_preview()
            self.update_ui_diff()

            # update the window title
            dt_str = self.old_data[1]
            dt = history_timestring_to_datetime(dt_str)
            tab_date = '[' + human_date(dt) + ']'
            self.setWindowTitle(' '.join([WINDOW_TITLE, '-', self.current_note.title, tab_date]))

    def update_ui_preview(self):
        content = self.noteEditor.toPlainText()
        html = self.generate_html(content)
        self.ui.notePreview.setSearchPaths([self.notes_dir])
        self.ui.notePreview.setHtml(html)
        if self.current_note is not None:
            self.ui.notePreview.setDocumentTitle(self.current_note.title)  # for things like print to pdf
        self.ui.notePreview.reload()

    def update_ui_diff(self):
        if self.old_data is not None:
            new_content = self.current_note.content
            content, __ = NoteModel.parse_note_content(self.old_data[0])
            dt_str = self.old_data[1]
            dt = history_timestring_to_datetime(dt_str)
            tab_date = '[' + human_date(dt) + ']'
            fromdesc = ' '.join([self.current_note.title, tab_date])
            diff_html = diff_to_html(content, new_content, fromdesc, self.current_note.title)
        else:
            try:
                diff_html = self.current_note.get_status()
            except AttributeError:
                # current_note is None
                diff_html = ''
        self.ui.noteDiff.setHtml(diff_html)
        if self.current_note is not None:
            self.ui.noteDiff.setDocumentTitle(self.current_note.title)  # for things like print to pdf
        self.ui.noteDiff.reload()

    def update_ui_historyLabel(self):
        color = 'rgb({0}, {1}, {2}, {3})'.format(*MOTOME_BLUE.getRgb())
        try:
            l = len(self.current_note.history)
        except AttributeError:
            l = 0

        self.ui.historyLabel.setText('<a href="#" style="color: {color}">{num} {version}</a>'.format(
            color=color,
            num=l,
            version='versions' if l != 1 else 'version'))

    def update_notesLocationsList(self):
        self.notesLocationsList.clear()
        self.notesLocationsList.addItems(sorted(self.conf['conf_notesLocations'].values()))
        if self.notes_dir != '':
            idx = self.notesLocationsList.findText(self.conf['conf_notesLocations'][self.notes_dir])
            if idx != -1:
                self.notesLocationsList.setCurrentIndex(idx)
        else:
            self.notesLocationsList.setCurrentIndex(0)

    def generate_html(self, content):
        try:
            header = build_preview_header_html(self.current_note.metadata['title'])
        except (AttributeError, KeyError, TypeError):
            # no title in metadata or no metadata
            header = build_preview_header_html('')
        body = self.md.convert(content)  # TODO: getting re MemoryErrors for large files
        footer = build_preview_footer_html()
        html = header + body + footer
        return html

    def export_html(self):
        html = self.generate_html(self.noteEditor.toPlainText())
        urls = self.noteEditor.get_note_links()
        media_urls = [url for url in urls if MEDIA_FOLDER in url[1]]
        export_dir = os.path.join(self.notes_dir, HTML_FOLDER, self.current_note.safename)
        stylesheets_dir = os.path.join(export_dir, 'stylesheets')
        media_dir = os.path.join(export_dir, MEDIA_FOLDER)
        dirs_to_make = [export_dir, stylesheets_dir, media_dir]
        # make the needed directories
        for d in dirs_to_make:
            try:
                os.makedirs(d)
            except OSError:
                pass
        # copy the needed files
        shutil.copy(os.path.join(self.style_dir, 'preview.css'), os.path.join(stylesheets_dir, 'preview.css'))
        for mediapath in media_urls:
            filename = os.path.basename(mediapath[1])
            shutil.copy(os.path.join(self.notes_dir, MEDIA_FOLDER, filename), os.path.join(media_dir, filename))
        htmlpath = os.path.join(export_dir, self.current_note.safename + HTML_EXTENSION)
        self._write_file(htmlpath, html)

        message_box = QtGui.QMessageBox()
        message_box.setTextFormat(QtCore.Qt.RichText)
        message_box.setWindowTitle("HTML Export Complete")
        message_box.setText("<center><b>HTML Export Complete</b></center>")
        message_box.setInformativeText('<center>Click to open the export directory<br>'
                                       '<a href="file:///{0}">{0}</a></center>'.format(export_dir))
        ok_btn = message_box.addButton(QtGui.QMessageBox.Ok)
        message_box.setDefaultButton(ok_btn)

        message_box.exec_()

    def start_meta_save(self):
        if self.save_meta_timer.isActive():
            self.save_meta_timer.stop()
        self.save_meta_timer.start(self.save_meta_interval)

    def save_note_meta(self):
        if self.noteEditor.save_timer.isActive():
            self.noteEditor.save_note()

        if self.save_meta_timer.isActive():
            self.save_meta_timer.stop()

        metadata = self.current_note.metadata

        rename = False
        if self.first_line_title:
            t = clean_filename(self.current_note.first_line, '').strip()
            if 'title' not in metadata.keys() or metadata['title'] != t:
                metadata['title'] = t
                rename = True

        metadata['tags'] = self.tagEditor.text()

        if 'conf_author' in self.conf.keys():
            metadata['author'] = self.conf['conf_author']

        # update the metadata
        self.current_note.metadata = metadata

        if rename:
            self.notesList.rename_current_item()

        # update settings button icon
        self.ui.btnSettings.setIcon(self.setting_button_icons['unsaved'])

    def save_the_unsaved(self):
        heathens = (nw.notemodel for nw in self.notesList.all_items if not nw.notemodel.is_saved)
        for unsaved in heathens:
            unsaved.save_to_file()

        # update settings button icon
        self.ui.btnSettings.setIcon(self.setting_button_icons['default'])

    def record_current_note(self):
        if not self.current_note.recorded:
            self.current_note.record()
            self.load_history_data()
            self.update_ui_historyLabel()

    def pin_current_note(self):
        if self.current_note.pinned:
            self.current_note.pinned = False
        else:
            self.current_note.pinned = True
        self.notesList.update_list()

    def print_current_pane(self):
        pane_num = self.ui.toolBox.currentIndex()
        printer = QtGui.QPrinter()
        print_dialog = QtGui.QPrintDialog(printer, self)

        if print_dialog.exec_() == QtGui.QDialog.Accepted:
            if pane_num == 0:
                self.noteEditor.print_(printer)
            elif pane_num == 1:
                self.ui.notePreview.print_(printer)
            elif pane_num == 2:
                self.ui.noteDiff.print_(printer)

    def new_note(self):
        tagged_title = self.ui.omniBar.text()
        if tagged_title == '':
            return
        if len(self.notesList.findItems(tagged_title, QtCore.Qt.MatchWildcard)) > 0:
            return

        # build new note name
        self.search.query = tagged_title

        if len(self.search.use_words) == 0:
            # no words to use in the title
            return

        title = ' '.join(self.search.use_words)
        tags = ' '.join(self.search.use_tags)

        # build the new note
        filename = clean_filename(title) + NOTE_EXTENSION
        filepath = os.path.join(self.notes_dir, filename)
        content = title + '\n'
        new_note = NoteModel(filepath)
        new_note.metadata['title'] = title
        new_note.metadata['tags'] = tags
        new_note.content = content

        # update
        new_note.save_to_file()
        self.notesList.update_list()

        self.ui.omniBar.setText('')
        self.query = ''
        try:
            item = self.notesList.findItems(tagged_title, QtCore.Qt.MatchWildcard)[0]
            self.notesList.setCurrentItem(item)
        except IndexError:
            for item in self.notesList.all_items[::-1]:
                if not item.notemodel.pinned:
                    self.notesList.setCurrentItem(item)

        # set the focus on the editor and move the cursor to the end
        self.noteEditor.setFocus()
        cursor = self.noteEditor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End, QtGui.QTextCursor.MoveMode.MoveAnchor)
        self.noteEditor.setTextCursor(cursor)

    def load_anchor(self, url):
        url_path = url.path()

        # intranote link?
        f = self.notesList.findItems(url_path, QtCore.Qt.MatchWildcard)
        try:
            self.notesList.setCurrentItem(f[0])
            return
        except IndexError:
            pass

        media_path = os.path.join(self.notes_dir, MEDIA_FOLDER, url_path.split('/')[-1])
        if os.path.isfile(media_path):
            ret = QtGui.QDesktopServices.openUrl(QtCore.QUrl('file:///' + media_path, QtCore.QUrl.TolerantMode))
        else:
            ret = QtGui.QDesktopServices.openUrl(url)

        if not ret:
            message_box = QtGui.QMessageBox()
            message_box.setText("Cannot open link.")
            message_box.setInformativeText('The link at {0} cannot be opened.'.format(media_path))
            ok_btn = message_box.addButton(QtGui.QMessageBox.Ok)
            message_box.setDefaultButton(ok_btn)

            message_box.exec_()

    def load_history_data(self):
        """
        Updates the history slider with history info from the current note
        """
        self.ui.historySlider.blockSignals(True)
        try:
            hlen = len(self.current_note.history)
        except AttributeError:
            hlen = 0
        self.ui.historySlider.setMaximum(hlen)
        self.ui.historySlider.setValue(hlen)
        self.ui.historySlider.blockSignals(False)

    def load_old_note(self, sliderpos):
        if sliderpos == self.ui.historySlider.maximum():
            self.update_ui_views()
            self.old_data = None
        else:
            self.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            self.old_data = self.current_note.load_old_note(sliderpos)
            self.update_ui_views_history()
            self.unsetCursor()

    def click_older_date(self):
        sliderpos = self.ui.historySlider.sliderPosition()
        if sliderpos != self.ui.historySlider.minimum():
            self.ui.historySlider.setValue(sliderpos - 1)
            self.load_old_note(sliderpos - 1)

    def click_newer_date(self):
        sliderpos = self.ui.historySlider.sliderPosition()
        if sliderpos != self.ui.historySlider.maximum():
            self.ui.historySlider.setValue(sliderpos + 1)
            self.load_old_note(sliderpos + 1)

    def start_search(self, query):
        self.query = query

        if len(query) > 2 and query[:-1] == ' ':
            self.search_notes()

        if self.search_timer.isActive():
            self.search_timer.stop()
        self.search_timer.start(self.search_interval)

    def search_notes(self):
        if self.search_timer.isActive():
            self.search_timer.stop()
        if self.query is None or self.query == '' or len(self.query) < 3:
            self.notesList.show_all()
        else:
            self.search.query = self.query.lower()
            self.notesList.search_noteitems(self.search)

    def delete_current_note(self):
        self.notesList.delete_current_item()

    def toggle_omnibar_view(self):
        if self.ui.frameOmniSettings.isHidden():
            self.ui.frameOmniSettings.show()
        else:
            self.ui.frameOmniSettings.hide()

    def toggle_history_bar_view(self):
        if self.ui.frameHistory.isHidden():
            self.ui.frameHistory.show()
        else:
            self.ui.frameHistory.hide()

    def toggle_notes_list_view(self):
        current_size = self.ui.splitter.sizes()
        if current_size[0] == 0 and self.notes_list_splitter_size is not None:
            self.ui.splitter.setSizes(self.notes_list_splitter_size)
            self.notes_list_splitter_size = None
        elif current_size[0] == 0 and self.notes_list_splitter_size is None:
            self.notes_list_splitter_size = current_size
            self.ui.splitter.setSizes([256, current_size[1]])
        elif self.notes_list_splitter_size is not None:
            self.notes_list_splitter_size = None
            self.ui.splitter.setSizes([0, current_size[1]])
        elif self.notes_list_splitter_size is None:
            self.notes_list_splitter_size = self.ui.splitter.sizes()
            self.ui.splitter.setSizes([0, current_size[1]])
        else:
            logger.warning('Toggle notes list view wierdness {0}'.format(self.notes_list_splitter_size))

    def show_default_notes_dir_message(self):
        message_box = QtGui.QMessageBox()
        message_box.setTextFormat(QtCore.Qt.RichText)
        message_box.setWindowTitle("Using default notes directory")
        message_box.setText("<center><b>Using Default Notes Directory</b></center>")
        message_box.setInformativeText('<center>No location was selected for your note files.  '
                                       'The default directory is being used.<br>'
                                       '<a href="file:///{0}">{0}</a></center>'.format(self.notes_dir))
        ok_btn = message_box.addButton(QtGui.QMessageBox.Ok)
        message_box.setDefaultButton(ok_btn)

        message_box.exec_()

    def show_custom_preview_menu(self, point):
        preview_rclk_menu = self.ui.notePreview.createStandardContextMenu()
        preview_rclk_menu.addSeparator()

        export_html_act = preview_rclk_menu.addAction(QtGui.QIcon(":/icons/resources/html.png"), 'Export HTML')
        export_html_act.triggered.connect(self.export_html)

        preview_rclk_menu.addSeparator()

        act_edit = preview_rclk_menu.addAction('Show Editor')
        act_edit.setShortcut(self.keyboard_shortcuts['ShowEdit']['seq'])
        act_edit.triggered.connect(self.keyboard_shortcuts['ShowEdit']['func'])

        act_diff = preview_rclk_menu.addAction('Show Diff')
        act_diff.setShortcut(self.keyboard_shortcuts['ShowDiff']['seq'])
        act_diff.triggered.connect(self.keyboard_shortcuts['ShowDiff']['func'])

        preview_rclk_menu.exec_(self.ui.notePreview.mapToGlobal(point))
        del preview_rclk_menu

    def show_custom_editor_menu(self, point):
        editor_rclk_menu = self.noteEditor.createStandardContextMenu()
        editor_rclk_menu.addSeparator()

        act_inslink = editor_rclk_menu.addAction('Insert Hyperlink')
        act_inslink.setShortcut(self.noteEditor.keyboard_shortcuts['InsLink']['seq'])
        act_inslink.triggered.connect(self.noteEditor.keyboard_shortcuts['InsLink']['func'])

        act_insfile = editor_rclk_menu.addAction('Insert File')
        act_insfile.setShortcut(self.noteEditor.keyboard_shortcuts['InsFile']['seq'])
        act_insfile.triggered.connect(self.noteEditor.keyboard_shortcuts['InsFile']['func'])

        editor_rclk_menu.addSeparator()

        act_preview = editor_rclk_menu.addAction('Show Preview')
        act_preview.setShortcut(self.keyboard_shortcuts['ShowPre']['seq'])
        act_preview.triggered.connect(self.keyboard_shortcuts['ShowPre']['func'])

        act_diff = editor_rclk_menu.addAction('Show Diff')
        act_diff.setShortcut(self.keyboard_shortcuts['ShowDiff']['seq'])
        act_diff.triggered.connect(self.keyboard_shortcuts['ShowDiff']['func'])

        editor_rclk_menu.exec_(self.noteEditor.mapToGlobal(point))
        del editor_rclk_menu

    def show_custom_diff_menu(self, point):
        diff_rclk_menu = self.noteEditor.createStandardContextMenu()
        diff_rclk_menu.addSeparator()

        act_edit = diff_rclk_menu.addAction('Show Editor')
        act_edit.setShortcut(self.keyboard_shortcuts['ShowEdit']['seq'])
        act_edit.triggered.connect(self.keyboard_shortcuts['ShowEdit']['func'])

        act_preview = diff_rclk_menu.addAction('Show Preview')
        act_preview.setShortcut(self.keyboard_shortcuts['ShowPre']['seq'])
        act_preview.triggered.connect(self.keyboard_shortcuts['ShowPre']['func'])

        diff_rclk_menu.exec_(self.noteEditor.mapToGlobal(point))
        del diff_rclk_menu