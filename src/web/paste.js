/* global EFDRC */
(function () {
  'use strict'

  const appendScript = function (document, src, onLoad) {
    const scriptEl = document.createElement('script')
    scriptEl.setAttribute('src', src)
    scriptEl.addEventListener('load', onLoad)
    document.body.appendChild(scriptEl)
  }

  const _pasteHTML = function (iframe, html, internal) {
    const outHtml = iframe.contentWindow.filterHTML(html, internal, false)
    document.execCommand('inserthtml', false, outHtml)
  }

  EFDRC.pasteHTML = function (html, internal) {
    // import editor js in an invisible iframe
    // to prevent reviewer window from being modified
    const existingIframe = document.getElementById('EFDRC-iframe')
    if (existingIframe) {
      // reuse existing iframe
      _pasteHTML(existingIframe, html, internal)
      return
    }

    const iframe = document.createElement('iframe')
    iframe.setAttribute('id', 'EFDRC-iframe')
    iframe.style.display = 'none'
    document.body.appendChild(iframe)
    const iframeDoc = iframe.contentDocument
    iframeDoc.body.innerHTML = '<div id="topbuts"></div><div id="fields"></div>'

    const getEditorJsAndPaste = function () {
      // filterHTML is declared as a let, and is not attached to the window object.
      // So we modify the script to attach it to the window object
      window.fetch('/_anki/js/editor.js')
        .then(response => {
          if (response.ok) return response.text()
          else {
            window.alert('ERROR: Edit Field During Review (Cloze) addon may not be compatible with this Anki version')
          }
        })
        .then(text => {
          const scriptEl = iframeDoc.createElement('script')
          scriptEl.innerHTML = text + '\nwindow.filterHTML = filterHTML'
          iframeDoc.body.appendChild(scriptEl)
          // run after contents were loaded and run
          _pasteHTML(iframe, html, internal)
        })
    }

    appendScript(iframeDoc, '/_anki/js/vendor/jquery.js', getEditorJsAndPaste)
  }
})()
