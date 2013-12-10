# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '..\Motome\Views\SettingsDialog.ui'
#
# Created: Tue Dec 10 11:33:54 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName("SettingsDialog")
        SettingsDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        SettingsDialog.resize(578, 348)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/resources/logo_320x320.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        SettingsDialog.setWindowIcon(icon)
        SettingsDialog.setModal(True)
        self.verticalLayout_2 = QtGui.QVBoxLayout(SettingsDialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tabWidget = QtGui.QTabWidget(SettingsDialog)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout = QtGui.QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_3 = QtGui.QLabel(self.tab)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.conf_notesLocation = QtGui.QLineEdit(self.tab)
        self.conf_notesLocation.setObjectName("conf_notesLocation")
        self.horizontalLayout.addWidget(self.conf_notesLocation)
        self.pushButton = QtGui.QPushButton(self.tab)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.conf_checkbox_preview = QtGui.QCheckBox(self.tab)
        self.conf_checkbox_preview.setChecked(True)
        self.conf_checkbox_preview.setObjectName("conf_checkbox_preview")
        self.verticalLayout.addWidget(self.conf_checkbox_preview)
        self.conf_checkbox_diff = QtGui.QCheckBox(self.tab)
        self.conf_checkbox_diff.setChecked(True)
        self.conf_checkbox_diff.setObjectName("conf_checkbox_diff")
        self.verticalLayout.addWidget(self.conf_checkbox_diff)
        self.conf_checkbox_history = QtGui.QCheckBox(self.tab)
        self.conf_checkbox_history.setChecked(True)
        self.conf_checkbox_history.setTristate(False)
        self.conf_checkbox_history.setObjectName("conf_checkbox_history")
        self.verticalLayout.addWidget(self.conf_checkbox_history)
        self.conf_checkbox_merge = QtGui.QCheckBox(self.tab)
        self.conf_checkbox_merge.setChecked(True)
        self.conf_checkbox_merge.setObjectName("conf_checkbox_merge")
        self.verticalLayout.addWidget(self.conf_checkbox_merge)
        self.conf_checkbox_deleteempty = QtGui.QCheckBox(self.tab)
        self.conf_checkbox_deleteempty.setChecked(True)
        self.conf_checkbox_deleteempty.setObjectName("conf_checkbox_deleteempty")
        self.verticalLayout.addWidget(self.conf_checkbox_deleteempty)
        self.tabWidget.addTab(self.tab, "")
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.tab_3)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label = QtGui.QLabel(self.tab_3)
        self.label.setOpenExternalLinks(True)
        self.label.setObjectName("label")
        self.verticalLayout_4.addWidget(self.label)
        self.textMarkdownHelp = QtGui.QTextBrowser(self.tab_3)
        self.textMarkdownHelp.setReadOnly(True)
        self.textMarkdownHelp.setAcceptRichText(False)
        self.textMarkdownHelp.setSource(QtCore.QUrl("qrc:/icons/resources/markdown_help.html"))
        self.textMarkdownHelp.setObjectName("textMarkdownHelp")
        self.verticalLayout_4.addWidget(self.textMarkdownHelp)
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.verticalLayout_5 = QtGui.QVBoxLayout(self.tab_4)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.textBrowser = QtGui.QTextBrowser(self.tab_4)
        self.textBrowser.setSource(QtCore.QUrl("qrc:/icons/resources/keyboard_shortcuts.html"))
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout_5.addWidget(self.textBrowser)
        self.tabWidget.addTab(self.tab_4, "")
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.tab_2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.textBrowser_2 = QtGui.QTextBrowser(self.tab_2)
        self.textBrowser_2.setSource(QtCore.QUrl("qrc:/icons/resources/about.html"))
        self.textBrowser_2.setObjectName("textBrowser_2")
        self.verticalLayout_3.addWidget(self.textBrowser_2)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout_2.addWidget(self.tabWidget)
        self.buttonBox = QtGui.QDialogButtonBox(SettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(SettingsDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), SettingsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), SettingsDialog.reject)
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL("clicked()"), SettingsDialog.load_folder_location)
        QtCore.QObject.connect(self.conf_checkbox_history, QtCore.SIGNAL("clicked(bool)"), self.conf_checkbox_diff.setChecked)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        SettingsDialog.setWindowTitle(QtGui.QApplication.translate("SettingsDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("SettingsDialog", "Notes location", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_notesLocation.setPlaceholderText(QtGui.QApplication.translate("SettingsDialog", "Please select a notes location...", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("SettingsDialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_preview.setText(QtGui.QApplication.translate("SettingsDialog", "Show Preview Tab", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_diff.setText(QtGui.QApplication.translate("SettingsDialog", "Show Diff Tab", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_history.setText(QtGui.QApplication.translate("SettingsDialog", "Show History Bar", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_merge.setText(QtGui.QApplication.translate("SettingsDialog", "Show Merge Notes Button", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_deleteempty.setToolTip(QtGui.QApplication.translate("SettingsDialog", "Should notes that contain no content be deleted, including their history?", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_deleteempty.setText(QtGui.QApplication.translate("SettingsDialog", "Delete empty notes", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("SettingsDialog", "Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("SettingsDialog", "<html><head/><body><p><a href=\"http://daringfireball.net/projects/markdown/syntax\"><span style=\" text-decoration: underline; color:#0000ff;\">See official syntax for details</span></a></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.textMarkdownHelp.setHtml(QtGui.QApplication.translate("SettingsDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><title>Markdown Help</title><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:7.8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:16px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:x-large; font-weight:600;\">Headers</span> </p>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">This is an H1</span></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">=============</span></pre>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">This is an H2</span></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">-------------</span></pre>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\"># This is an H1</span></pre>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">## This is an H2</span></pre>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">###### This is an H6</span> </pre>\n"
"<p style=\" margin-top:16px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:x-large; font-weight:600;\">Paragraphs</span> </p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">A paragraph is simply one or more consecutive lines of text, separated by one or more blank lines. </p>\n"
"<p style=\" margin-top:16px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:x-large; font-weight:600;\">Emphasis</span> </p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:medium; font-weight:600;\">Italics</span> </p>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">*single asterisks*</span></pre>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">_single underscores_</span> </pre>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:medium; font-weight:600;\">Bold</span> </p>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">**double asterisks**</span></pre>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">__double underscores__</span> </pre>\n"
"<p style=\" margin-top:16px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:x-large; font-weight:600;\">Links</span> </p>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">This is [an example](http://example.com/ &quot;Title&quot;) inline link.</span></pre>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">[This link](http://example.net/) has no title attribute.</span> </pre>\n"
"<p style=\" margin-top:16px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:x-large; font-weight:600;\">Lists</span> </p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:medium; font-weight:600;\">Bullet</span> </p>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">*   Red</span></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">*   Green</span></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">*   Blue</span> </pre>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:medium; font-weight:600;\">Numbered</span> </p>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">1.  Bird</span></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">2.  McHale</span></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">3.  Parish</span> </pre>\n"
"<p style=\" margin-top:16px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:x-large; font-weight:600;\">Images</span> </p>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">![Alt text](/path/to/img.jpg)</span></pre>\n"
"<pre style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Courier New,courier\';\"><br /></pre>\n"
"<pre style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New,courier\';\">![Alt text](/path/to/img.jpg &quot;Optional title&quot;)</span> </pre></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("SettingsDialog", "Markdown Help", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QtGui.QApplication.translate("SettingsDialog", "Keyboard Shortcuts", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("SettingsDialog", "About", None, QtGui.QApplication.UnicodeUTF8))

import MainWindow_rc
