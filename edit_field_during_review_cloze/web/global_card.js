
(function () {
  const EFDRC = {}
  window.EFDRC = EFDRC

  EFDRC.CTRL = '%(ctrl)s' // bool
  EFDRC.PASTE = '%(paste)s' // bool
  EFDRC.SPAN = '%(span)s' // bool
  EFDRC.REMSPAN = '%(remove_span)s' // bool
  EFDRC.SPECIAL = JSON.parse('%(special)s') // array of array

  EFDRC.specials_noctrl = {
    // shift, alt, key, command, has arg?
    strikethrough: [true, true, 'Digit5', 'strikeThrough', false],
    fontcolor: [false, false, 'F7', 'foreColor', true]
  }

  EFDRC.specials_ctrl = {
    // shift, alt, key, command, has arg
    removeformat: [false, false, 'KeyR', 'removeFormat', false],
    highlight: [true, false, 'KeyB', 'hiliteColor', true],
    subscript: [false, false, 'Equal', 'subscript', false],
    superscript: [true, false, 'Equal', 'superscript', false],
    formatblock: [false, false, 'Period', 'formatBlock', true],
    hyperlink: [true, false, 'KeyH', 'createLink', false],
    unhyperlink: [true, true, 'KeyH', 'createLink', false],
    unorderedlist: [false, false, 'BracketLeft', 'insertUnorderedList', false],
    orderedlist: [false, false, 'BracketRight', 'insertOrderedList', false],
    indent: [true, false, 'BracketRight', 'indent', false],
    outdent: [true, false, 'BracketLeft', 'outdent', false],
    justifyCenter: [true, true, 'KeyS', 'justifyCenter', false],
    justifyLeft: [true, true, 'KeyL', 'justifyLeft', false],
    justifyRight: [true, true, 'KeyR', 'justifyRight', false],
    justifyFull: [true, true, 'KeyB', 'justifyFull', false]
  }

  // wrappedExceptForWhitespace, wrapInternal from /anki/editor.ts
  EFDRC.wrappedExceptForWhitespace = function (text, front, back) {
    const match = text.match(/^(\s*)([^]*?)(\s*)$/)
    return match[1] + front + match[2] + back + match[3]
  }

  EFDRC.wrapInternal = function (front, back) {
    if (document.activeElement.dir === 'rtl') {
      front = '&#8235;' + front + '&#8236;'
      back = '&#8235;' + back + '&#8236;'
    }
    const s = window.getSelection()
    let r = s.getRangeAt(0)
    const content = r.cloneContents()
    const span = document.createElement('span')
    span.appendChild(content)
    const new_ = EFDRC.wrappedExceptForWhitespace(span.innerText, front, back)
    document.execCommand('inserttext', false, new_)
    if (!span.innerHTML) {
      // run with an empty selection; move cursor back past postfix
      r = s.getRangeAt(0)
      r.setStart(r.startContainer, r.startOffset - back.length)
      r.collapse(true)
      s.removeAllRanges()
      s.addRange(r)
    }
  }

  EFDRC.b64DecodeUnicode = function (str) {
    return decodeURIComponent(window.atob(str).split('').map(function (c) {
      return '%%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join(''))
  }

  EFDRC.removeSpan = function (el) {
    // removes all span code because depending on the note type
    // pressing backspace can wrap the text in span and apply different styling.
    const elems = el.getElementsByTagName('span')
    for (let x = 0; x < elems.length; x++) {
      const span = elems[x]
      const children = span.childNodes
      for (let y = 0; y < children.length; y++) {
        // insert after node so caret position is maintained. If last sibling, inserted at end.
        span.parentNode.insertBefore(children[y], span.nextSibling)
      }
      span.parentNode.removeChild(span)
    }
  }

  EFDRC.handlePaste = function (e) {
    const mimetype = ['text/html', 'image/', 'video/', 'audio/', 'application/']
    const paste = (e.clipboardData || window.clipboardData)
    for (let x = 0; x < paste.types.length; x++) {
      const mtype = paste.types[x]
      let toSend = false
      for (let y = 0; y < mimetype.length; y++) {
        if (mtype.indexOf(mimetype[y]) !== -1) {
          toSend = true
          break
        }
      }
      if (toSend) {
        e.preventDefault()
        window.pycmd('EFDRC!paste') // python code accesses clipboard
        break
      }
    }
  }

  EFDRC.ctrldown = function () {
    EFDRC.ctrlLinkEnable()
    if (EFDRC.CTRL) {
      const els = document.querySelectorAll("[data-EFDRC='true']")
      for (let e = 0; e < els.length; e++) {
        const el = els[e]
        el.setAttribute('contenteditable', 'true')
        if (el.hasAttribute('data-EFDRCnotctrl')) {
          el.removeAttribute('data-EFDRCnotctrl')
        }
      }
    }
  }

  EFDRC.ctrlup = function () {
    EFDRC.ctrlLinkDisable()
    if (EFDRC.CTRL) {
      const els = document.querySelectorAll("[data-EFDRC='true']")
      for (let e = 0; e < els.length; e++) {
        const el = els[e]
        if (el === document.activeElement) {
          el.setAttribute('data-EFDRCnotctrl', 'true')
        } else {
          el.setAttribute('contenteditable', 'false')
        }
      }
    }
  }

  EFDRC.placeholder = function (e) {
    const fldName = EFDRC.b64DecodeUnicode(e.getAttribute('data-EFDRCfield'))
    e.setAttribute('data-placeholder', fldName)
  }

  EFDRC.addListeners = function (e, fld) {
    if (EFDRC.PASTE) {
      e.addEventListener('paste', EFDRC.handlePaste)
    }

    e.addEventListener('focus', function (event) {
      if (typeof window.showTooltip === 'function' && typeof window.showTooltip2 === 'undefined') {
        // Disable Popup Dictionary addon tooltip on double mouse click.
        // Using hotkey should still work however.
        window.showTooltip2 = window.showTooltip
        window.showTooltip = function (event, tooltip, element) {
          EFDRC.tooltip = {
            ev: event,
            tt: tooltip,
            el: element
          }
        }
        window.showTooltip.hide = function () { }
        window.invokeTooltipAtSelectedElm2 = window.invokeTooltipAtSelectedElm
        window.invokeTooltipAtSelectedElm = function () {
          window.invokeTooltipAtSelectedElm2()
          window.showTooltip2(EFDRC.tooltip.ev, EFDRC.tooltip.tt, EFDRC.tooltip.el)
        }
      }

      window.pycmd('EFDRC!focuson#' + fld)
    })
    e.addEventListener('blur', function (event) {
      if (typeof showTooltip2 === 'function') {
        // Restore Popup Dictionary
        window.showTooltip = window.showTooltip2
        delete window.showTooltip2
        window.invokeTooltipAtSelectedElm = window.invokeTooltipAtSelectedElm2
        delete window.invokeTooltipAtSelectedElm2
      }

      const el = event.currentTarget
      if (EFDRC.REMSPAN) {
        EFDRC.removeSpan(el)
      }
      if (el.hasAttribute('data-EFDRCnotctrl')) {
        el.removeAttribute('data-EFDRCnotctrl')
        el.setAttribute('contenteditable', 'false')
      }
      if (el.hasAttribute('data-EFDRCnid')) {
        EFDRC.cleanResize(el)
        window.pycmd('EFDRC#' + el.getAttribute('data-EFDRCnid') + '#' + el.getAttribute('data-EFDRCfield') + '#' + el.innerHTML)
        window.pycmd('EFDRC!reload')
      } else {
        window.pycmd('EFDRC!reload')
      }
    })

    e.addEventListener('keydown', function (event) {
      // Slightly faster.
      const ctrlKey = event.ctrlKey || event.metaKey
      const shiftKey = event.shiftKey
      const altKey = event.altKey
      const codeKey = event.code
      const el = event.currentTarget
      if (EFDRC.SPAN) {
        if (codeKey === 'Backspace') {
          event.stopPropagation()
        }
      }
      if (EFDRC.REMSPAN) {
        if (codeKey === 'Backspace' || codeKey === 'Delete') {
          setTimeout(function () {
            EFDRC.removeSpan(el)
          }, 0)
        }
      }

      if (event.code === 'KeyS' && event.altKey &&
                !event.shiftKey && !event.ctrlKey && !event.metaKey) {
        // image resizer
        EFDRC.resizeImageMode = !EFDRC.resizeImageMode
        EFDRC.maybeResizeOrClean()
        event.preventDefault()
        event.stopPropagation()
      }

      if (ctrlKey) {
        // cloze deletion, onCloze from aqt.editor
        if (event.code === 'KeyC' && shiftKey) {
          let highest = 0
          const val = el.innerHTML
          let m
          const myRe = /\{\{c(\d+)::/g
          while ((m = myRe.exec(val)) !== null) {
            highest = Math.max(highest, m[1])
          }
          if (!altKey) {
            highest += 1
          }
          highest = Math.max(1, highest)
          EFDRC.wrapInternal('{{c' + highest + '::', '}}')
          event.preventDefault()
        } else {
          // Special formatting that requires ctrl key.
          for (const special in EFDRC.specials_ctrl) {
            const specialVal = EFDRC.specials_ctrl[special]
            let enabled, parmVal
            if (specialVal[4]) {
              enabled = EFDRC.SPECIAL[special][0]
              parmVal = EFDRC.SPECIAL[special][1]
            } else {
              enabled = EFDRC.SPECIAL[special]
            }
            if (enabled) {
              const s = specialVal[0]
              const a = specialVal[1]
              const c = specialVal[2]
              if (shiftKey === s && altKey === a && codeKey === c) {
                if (specialVal[4]) {
                  document.execCommand(specialVal[3], false, parmVal)
                } else {
                  document.execCommand(specialVal[3], false)
                }
                event.preventDefault()
              }
            }
          }
        }
      } else {
        // Special formatting that doesn't require ctrl key
        for (const special in EFDRC.specials_noctrl) {
          const specialVal = EFDRC.specials_noctrl[special]
          let enabled, parmVal
          if (specialVal[4]) {
            enabled = EFDRC.SPECIAL[special][0]
            parmVal = EFDRC.SPECIAL[special][1]
          } else {
            enabled = EFDRC.SPECIAL[special]
          }
          if (enabled) {
            const s = specialVal[0]
            const a = specialVal[1]
            const c = specialVal[2]
            if (shiftKey === s && altKey === a && codeKey === c) {
              if (specialVal[4]) {
                document.execCommand(specialVal[3], false, parmVal)
              } else {
                document.execCommand(specialVal[3], false)
              }
              event.preventDefault()
            }
          }
        }
      }
    })
  }

  EFDRC.ctrlLinkEnable = function () {
    const links = document.querySelectorAll("[data-EFDRC='true'] a")
    for (let x = 0; x < links.length; x++) {
      const el = links[x]
      el.setAttribute('contenteditable', 'false')
    }
  }

  EFDRC.ctrlLinkDisable = function () {
    const links = document.querySelectorAll("[data-EFDRC='true'] a[contenteditable='false']")
    for (let x = 0; x < links.length; x++) {
      const el = links[x]
      el.removeAttribute('contenteditable')
    }
  }

  window.addEventListener('keydown', function (event) {
    if (['ControlLeft', 'MetaLeft'].includes(event.code)) {
      EFDRC.ctrldown()
    }
  })

  window.addEventListener('keyup', function (event) {
    if (['ControlLeft', 'MetaLeft'].includes(event.code)) {
      EFDRC.ctrlup()
    }
  })
})()
