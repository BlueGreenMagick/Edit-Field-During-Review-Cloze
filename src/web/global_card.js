(function () {
  const EFDRC = function () {
    this.specials_noctrl = {
      // shift, alt, key, command, has arg?
      strikethrough: [true, true, 'Digit5', 'strikeThrough', false],
      fontcolor: [false, false, 'F7', 'foreColor', true]
    }
    this.specials_ctrl = {
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
  }

  EFDRC.prototype = Object.create(null)
  // wrappedExceptForWhitespace, wrapInternal from /anki/editor.ts
  EFDRC.prototype.wrappedExceptForWhitespace = function (text, front, back) {
    const match = text.match(/^(\s*)([^]*?)(\s*)$/)
    return match[1] + front + match[2] + back + match[3]
  }
  EFDRC.prototype.wrapInternal = function (front, back) {
    if (document.activeElement.dir === 'rtl') {
      front = '&#8235;' + front + '&#8236;'
      back = '&#8235;' + back + '&#8236;'
    }
    const s = window.getSelection()
    let r = s.getRangeAt(0)
    const content = r.cloneContents()
    const span = document.createElement('span')
    span.appendChild(content)
    const new_ = this.wrappedExceptForWhitespace(span.innerText, front, back)
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

  EFDRC.prototype.b64DecodeUnicode = function (str) {
    return decodeURIComponent(window.atob(str).split('').map(function (c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join(''))
  }

  EFDRC.prototype.removeSpan = function (el) {
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

  EFDRC.prototype.handlePaste = function (e) {
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

  EFDRC.prototype.ctrldown = function () {
    this.ctrlLinkEnable()
    if (this.CTRL) {
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

  EFDRC.prototype.ctrlup = function () {
    this.ctrlLinkDisable()
    if (this.CTRL) {
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

  EFDRC.prototype.placeholder = function (e) {
    const fldName = this.b64DecodeUnicode(e.getAttribute('data-EFDRCfield'))
    e.setAttribute('data-placeholder', fldName)
  }

  EFDRC.prototype.addListeners = function (e, fld) {
    if (this.PASTE) {
      e.addEventListener('paste', this.handlePaste)
    }

    e.addEventListener('focus', function (event) {
      if (typeof window.showTooltip === 'function' && typeof window.showTooltip2 === 'undefined') {
        // Disable Popup Dictionary addon tooltip on double mouse click.
        // Using hotkey should still work however.
        window.showTooltip2 = window.showTooltip
        window.showTooltip = function (event, tooltip, element) {
          window.EFDRC.tooltip = {
            ev: event,
            tt: tooltip,
            el: element
          }
        }
        window.showTooltip.hide = function () { }
        window.invokeTooltipAtSelectedElm2 = window.invokeTooltipAtSelectedElm
        window.invokeTooltipAtSelectedElm = function () {
          window.invokeTooltipAtSelectedElm2()
          window.showTooltip2(this.tooltip.ev, this.tooltip.tt, this.tooltip.el)
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
      if (this.REMSPAN) {
        this.removeSpan(el)
      }
      if (el.hasAttribute('data-EFDRCnotctrl')) {
        el.removeAttribute('data-EFDRCnotctrl')
        el.setAttribute('contenteditable', 'false')
      }
      if (el.hasAttribute('data-EFDRCnid')) {
        this.cleanResize(el)
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
      if (this.SPAN) {
        if (codeKey === 'Backspace') {
          event.stopPropagation()
        }
      }
      if (this.REMSPAN) {
        if (codeKey === 'Backspace' || codeKey === 'Delete') {
          setTimeout(function () {
            EFDRC.removeSpan(el)
          }, 0)
        }
      }

      if (event.code === 'KeyS' && event.altKey &&
                !event.shiftKey && !event.ctrlKey && !event.metaKey) {
        // image resizer
        this.resizeImageMode = !this.resizeImageMode
        this.maybeResizeOrClean()
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
          this.wrapInternal('{{c' + highest + '::', '}}')
          event.preventDefault()
        } else {
          // Special formatting that requires ctrl key.
          for (const special in this.specials_ctrl) {
            const specialVal = this.specials_ctrl[special]
            let enabled, parmVal
            if (specialVal[4]) {
              enabled = this.SPECIAL[special][0]
              parmVal = this.SPECIAL[special][1]
            } else {
              enabled = this.SPECIAL[special]
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
        for (const special in this.specials_noctrl) {
          const specialVal = this.specials_noctrl[special]
          let enabled, parmVal
          if (specialVal[4]) {
            enabled = this.SPECIAL[special][0]
            parmVal = this.SPECIAL[special][1]
          } else {
            enabled = this.SPECIAL[special]
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

  EFDRC.prototype.ctrlLinkEnable = function () {
    const links = document.querySelectorAll("[data-EFDRC='true'] a")
    for (let x = 0; x < links.length; x++) {
      const el = links[x]
      el.setAttribute('contenteditable', 'false')
    }
  }

  EFDRC.prototype.ctrlLinkDisable = function () {
    const links = document.querySelectorAll("[data-EFDRC='true'] a[contenteditable='false']")
    for (let x = 0; x < links.length; x++) {
      const el = links[x]
      el.removeAttribute('contenteditable')
    }
  }

  EFDRC.prototype.registerConfig = function (confStr) {
    const conf = JSON.parse(confStr)
    console.log(conf)
    if (conf.tag === 'span') {
      this.SPAN = true
    } else {
      this.SPAN = false
    }
    this.SPAN = conf.tag
    this.CTRL = conf.ctrl_click
    this.PASTE = conf.process_paste
    this.REMSPAN = conf.remove_span
    this.DEFAULTRESIZE = conf.resize_image_default_state
    this.SPECIAL = conf.z_special_formatting
    this.preserve_ratio = conf.resize_image_preserve_ratio
  }

  EFDRC.prototype.serveCard = function (fld) { // fld: string
    const els = document.querySelectorAll("[data-EFDRCfield='" + fld + "']")
    for (let e = 0; e < els.length; e++) {
      const el = els[e]
      this.addListeners(el, fld)
      if (this.CTRL) {
        this.placeholder(el)
      }
    }

    if (!this.CTRL) {
      for (let e = 0; e < els.length; e++) {
        els[e].setAttribute('contenteditable', 'true')
      }
    }
  }

  window.EFDRC = new EFDRC()

  window.addEventListener('keydown', function (event) {
    if (['ControlLeft', 'MetaLeft'].includes(event.code)) {
      window.EFDRC.ctrldown()
    }
  })

  window.addEventListener('keyup', function (event) {
    if (['ControlLeft', 'MetaLeft'].includes(event.code)) {
      window.EFDRC.ctrlup()
    }
  })
})()
