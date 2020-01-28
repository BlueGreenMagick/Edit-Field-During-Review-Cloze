from anki.hooks import wrap

from aqt import mw
from aqt.qt import QCursor, Qt
from aqt.progress import ProgressManager
from aqt.editor import Editor, EditorWebView
from aqt.utils import showInfo, tooltip


class semiEditor(Editor):

    def __init__(self):
        self.mw = mw
        self.parentWindow = "EFDRCsemiedit"


class semiEditorWebView(EditorWebView):

    def __init__(self):
        self.mw = mw
        self.editor = semiEditor()


def mystart(*args, **kwargs):
    _old = kwargs.pop("_old")
    if "parent" in kwargs:
        parent = kwargs["parent"]
    elif len(args) > 4:
        parent = args[4]
    else:
        parent = None
    if parent == "EFDRCsemiedit":
        mw.EFDRCsemieditprogress = True
        mw.app.setOverrideCursor(QCursor(Qt.WaitCursor))
        return
    else:
        return _old(*args, **kwargs)


def myfinish(self, _old):
    if hasattr(mw,"EFDRCsemieditprogress") and mw.EFDRCsemieditprogress:
        mw.EFDRCsemieditprogress = False
        self.app.restoreOverrideCursor()
        return
    else:
        return _old(self)


ProgressManager.start = wrap(ProgressManager.start, mystart, "around")
ProgressManager.finish = wrap(ProgressManager.finish, myfinish, "around")
