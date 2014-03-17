
from PySide import QtCore, QtGui


class AutoCompleteEdit(QtGui.QLineEdit):
    """ Implements autocomplete on a QLineEdit with changeable completer list
    Many thanks to: https://bitbucket.org/3david/qtodotxt/src/ec1e74eef575/qtodotxt/ui/controls/autocomplete_lineedit.py
    """
    def __init__(self, model, separator=' ', addSpaceAfterCompleting = True):
        super(AutoCompleteEdit, self).__init__()
        self._separator = separator
        self._addSpaceAfterCompleting = addSpaceAfterCompleting
        self.completer = QtGui.QCompleter(model)
        self.completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
        self.completer.setWidget(self)
        self.connect(
                self.completer,
                QtCore.SIGNAL('activated(QString)'),
                self._insertCompletion)
        self._keysToIgnore = [QtCore.Qt.Key_Enter,
                              QtCore.Qt.Key_Return,
                              QtCore.Qt.Key_Escape,
                              QtCore.Qt.Key_Tab]

    def _insertCompletion(self, completion):
        """
        This is the event handler for the QCompleter.activated(QString) signal,
        it is called when the user selects an item in the completer popup.
        """
        extra = len(completion) - len(self.completer.completionPrefix())
        extra_text = completion[-extra:]
        if self._addSpaceAfterCompleting:
            extra_text += ' '
        self.setText(self.text() + extra_text)

    def textUnderCursor(self):
        text = self.text()
        textUnderCursor = ''
        i = self.cursorPosition() - 1
        while i >=0 and text[i] != self._separator:
            textUnderCursor = text[i] + textUnderCursor
            i -= 1
        return textUnderCursor

    def keyPressEvent(self, event):
        if self.completer.popup().isVisible():
            if event.key() in self._keysToIgnore:
                event.ignore()
                return
        super(AutoCompleteEdit, self).keyPressEvent(event)
        completionPrefix = self.textUnderCursor()
        if completionPrefix != self.completer.completionPrefix():
            self._updateCompleterPopupItems(completionPrefix)
        if len(event.text()) > 0:
            self.completer.complete()

    def _updateCompleterPopupItems(self, completionPrefix):
        """
        Filters the completer's popup items to only show items
        with the given prefix.
        """
        self.completer.setCompletionPrefix(completionPrefix)
        self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0,0))

    def setCompleterModel(self, items):
        self.completer.setModel(items)