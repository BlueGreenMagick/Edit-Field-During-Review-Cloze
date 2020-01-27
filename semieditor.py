from aqt.editor import Editor, EditorWebView
from aqt import mw



class semiEditor(Editor):
    
    def __init__(self):
        self.mw = mw
        self.parentWindow = mw


        

class semiEditorWebView(EditorWebView):
    
    def __init__(self):
        self.mw = mw
        self.editor = semiEditor()
        
        