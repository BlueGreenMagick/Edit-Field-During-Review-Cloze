from typing import Any, Callable, Optional

from anki.hooks import wrap
from aqt import mw
from aqt.editor import Editor, EditorWebView
from aqt.progress import ProgressManager, ProgressDialog
from aqt.qt import QCursor, Qt

# necessary in order to use methods defined in Editor and EditorWebView
# without setting up the UI


myprogress = False


class semiEditor(Editor):
    def __init__(self) -> None:
        self.mw = mw
        self.parentWindow = "EFDRCsemiedit"  # type: ignore


class semiEditorWebView(EditorWebView):
    def __init__(self) -> None:
        self.mw = mw
        self.editor = semiEditor()


def mystart(*args: Any, **kwargs: Any) -> Optional[ProgressDialog]:
    global myprogress
    _old = kwargs.pop("_old")
    if "parent" in kwargs:
        parent = kwargs["parent"]
    elif len(args) > 4:
        parent = args[4]  # Position of 'parent' parameter.
    else:
        parent = None

    if parent == "EFDRCsemiedit":
        # Don't show progress window when pasting images while in review.
        myprogress = True
        mw.app.setOverrideCursor(QCursor(Qt.WaitCursor))
        return None
    else:
        myprogress = False
        return _old(*args, **kwargs)


def myfinish(self: ProgressManager, _old: Callable) -> None:
    global myprogress
    if myprogress:
        myprogress = False
        self.app.restoreOverrideCursor()
        return
    else:
        return _old(self)


ProgressManager.start = wrap(ProgressManager.start, mystart, "around")  # type: ignore
ProgressManager.finish = wrap(ProgressManager.finish, myfinish, "around")  # type: ignore
