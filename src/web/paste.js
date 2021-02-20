(function () {
  'use strict'

  const appendScript = function (document, src, onLoad) {
    const scriptEl = document.createElement('script')
    scriptEl.setAttribute('src', src)
    scriptEl.addEventListener('load', onLoad)
    document.body.appendChild(scriptEl)
  }

  window.pasteHTML = function (html, internal) {
    // import editor js in an invisible iframe
    // to prevent reviewer window from being modified
    const iframe = document.createElement('iframe')
    iframe.style.display = 'none'
    document.body.appendChild(iframe)
    const iframeDoc = iframe.contentDocument
    iframeDoc.body.innerHTML = '<div id="topbuts"></div><div id="fields"></div>'

    // filterHTML is declared as a let, and is not attached to the window object.
    // So we modify the script to attach it to the window object
    const getEditorJsAndPaste = function () {
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
          const outHtml = iframe.contentWindow.filterHTML(html, internal, false)
          document.execCommand('inserthtml', false, outHtml)
        })
    }

    appendScript(iframeDoc, '/_anki/js/vendor/jquery.js', getEditorJsAndPaste)
  }
})()
