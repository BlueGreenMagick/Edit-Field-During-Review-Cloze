from aqt.editor import Editor, EditorWebView
from aqt import mw



class semiEditor():
    #Necessary methods/variables for handling paste
    _pastePreFilter = Editor._pastePreFilter
    removeTags = Editor.removeTags
    isURL = Editor.isURL
    _retrieveURL = Editor._retrieveURL
    inlinedImageToFilename = Editor.inlinedImageToFilename
    _addPastedImage = Editor._addPastedImage
    fnameToLink = Editor.fnameToLink
    _addMediaFromData = Editor._addMediaFromData
    urlToLink = Editor.urlToLink
    urlToFile = Editor.urlToFile
    inlinedImageToLink = Editor.inlinedImageToLink
    
    def __init__(self):
        self.mw = mw
        self.parentWindow = mw.web


        

class semiEditorWebView():
    #Necessary methods/variables for handling paste
    _processMime = EditorWebView._processMime
    _processUrls = EditorWebView._processUrls
    _processText = EditorWebView._processText
    _processImage = EditorWebView._processImage
    _processHtml = EditorWebView._processHtml
    
    def __init__(self):
        self.mw = mw
        self.editor = semiEditor()
        
        