from anki.hooks import wrap

from aqt import mw
from aqt.qt import QCursor, Qt
from aqt.progress import ProgressManager
from aqt.editor import Editor, EditorWebView


class semiEditor(Editor):

    def __init__(self):
        self.mw = mw
        self.parentWindow = "EFDRCsemiedit"


class semiEditorWebView(EditorWebView):

    def __init__(self):
        self.mw = mw
        self.editor = semiEditor()


def mystart(self, max=0, min=0, label=None, parent=None, immediate=False, _old=None):
    if parent == "EFDRCsemiedit":
        mw.EFDRCsemieditprogress = True
        self.mw.app.setOverrideCursor(QCursor(Qt.WaitCursor))
        return
    else:
        return _old(self, max=0, min=0, label=None, parent=None, immediate=False)


def myfinish(self, _old):
    if mw.EFDRCsemieditprogress:
        mw.EFDRCsemieditprogress = False
        self.app.restoreOverrideCursor()
        return
    else:
        return _old(self)


ProgressManager.start = wrap(ProgressManager.start, mystart, "around")
ProgressManager.finish = wrap(ProgressManager.finish, myfinish, "around")
