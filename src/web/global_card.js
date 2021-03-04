(function () {
  window.EFDRC = {}
  const EFDRC = window.EFDRC
  EFDRC.shortcuts = []

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
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
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
    if (!EFDRC.PASTE) {
      return
    }
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
      const els = document.querySelectorAll('[data-EFDRCfield]')
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
      const els = document.querySelectorAll('[data-EFDRCfield]')
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

  EFDRC.isInsideEfdrcDiv = function (el) {
    const hardBreak = 100
    let currentEl = el
    let i = 0
    while (currentEl instanceof window.Element && i < hardBreak) {
      if (currentEl.hasAttribute('data-EFDRCfield')) {
        return currentEl
      }
      currentEl = el.parentNode
      i++
    }
  }

  EFDRC.registerShortcut = function (shortcut, handler) {
    const shortcutKeys = shortcut.toLowerCase().split(/[+]/).map(key => key.trim())
    const modKeys = ['ctrl', 'shift', 'alt']
    const scutInfo = {}
    modKeys.forEach(modKey => { scutInfo[modKey] = shortcutKeys.includes(modKey) })
    let mainKey = shortcutKeys[shortcutKeys.length - 1]
    if (mainKey.length === 1) {
      if (/\d/.test(mainKey)) {
        mainKey = 'digit' + mainKey
      } else {
        mainKey = 'key' + mainKey
      }
    }
    scutInfo.key = mainKey
    scutInfo.handler = handler
    EFDRC.shortcuts.push(scutInfo)
  }

  EFDRC.setCloze = function (event, el, altKey) {
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
  }

  EFDRC.matchShortcut = function (event, scutInfo) {
    if (scutInfo.key !== event.code.toLowerCase()) return false
    if (scutInfo.ctrl !== (event.ctrlKey || event.metaKey)) return false
    if (scutInfo.shift !== event.shiftKey) return false
    if (scutInfo.alt !== event.altKey) return false
    return true
  }

  EFDRC.handleKeydown = function (event, target) {
    for (let i = 0; i < EFDRC.shortcuts.length; i++) {
      const scutInfo = EFDRC.shortcuts[i]
      if (EFDRC.matchShortcut(event, scutInfo)) {
        EFDRC.shortcuts[i].handler(event, target)
        event.preventDefault()
        event.stopPropagation()
      }
    }
  }

  EFDRC.handleFocus = function (event, target) {
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
    const fld = target.getAttribute('data-EFDRCfield')
    window.pycmd('EFDRC!focuson#' + fld)
  }

  EFDRC.handleBlur = function (event, target) {
    if (typeof showTooltip2 === 'function') {
      // Restore Popup Dictionary
      window.showTooltip = window.showTooltip2
      delete window.showTooltip2
      window.invokeTooltipAtSelectedElm = window.invokeTooltipAtSelectedElm2
      delete window.invokeTooltipAtSelectedElm2
    }

    const el = target
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
  }

  EFDRC.addListener = function (handlerInfo) {
    const eventName = handlerInfo[0]
    const handler = handlerInfo[1]
    window.addEventListener(eventName, function (event) {
      const target = EFDRC.isInsideEfdrcDiv(event.target)
      if (target) {
        handler(event, target)
      }
    })
  }

  EFDRC.handlers = [
    ['paste', EFDRC.handlePaste],
    ['focusin', EFDRC.handleFocus],
    ['focusout', EFDRC.handleBlur],
    ['keydown', EFDRC.handleKeydown]
  ]
  for (let i = 0; i < EFDRC.handlers.length; i++) {
    EFDRC.addListener(EFDRC.handlers[i])
  }

  EFDRC.ctrlLinkEnable = function () {
    const links = document.querySelectorAll('[data-EFDRCfield] a')
    for (let x = 0; x < links.length; x++) {
      const el = links[x]
      el.setAttribute('contenteditable', 'false')
    }
  }

  EFDRC.ctrlLinkDisable = function () {
    const links = document.querySelectorAll("[data-EFDRCfield] a[contenteditable='false']")
    for (let x = 0; x < links.length; x++) {
      const el = links[x]
      el.removeAttribute('contenteditable')
    }
  }

  EFDRC.registerConfig = function (confStr) {
    const conf = JSON.parse(confStr)
    console.log(conf)
    if (conf.tag === 'span') {
      EFDRC.SPAN = true
    } else {
      EFDRC.SPAN = false
    }
    EFDRC.SPAN = conf.tag
    EFDRC.CTRL = conf.ctrl_click
    EFDRC.PASTE = conf.process_paste
    EFDRC.REMSPAN = conf.remove_span
    EFDRC.DEFAULTRESIZE = conf.resize_image_default_state
    EFDRC.SPECIAL = conf.z_special_formatting
    EFDRC.preserve_ratio = conf.resize_image_preserve_ratio
    for (const key in conf.z_special_formatting) {
      const format = conf.z_special_formatting[key]
      if (!format.enabled) {
        continue
      }
      const shortcut = format.shortcut
      const args = [format.command, false].concat(format.args)
      EFDRC.registerShortcut(shortcut, () => { document.execCommand.apply(document, args) }) // spread args list
    }
  }

  EFDRC.serveCard = function (fld) { // fld: string
    const els = document.querySelectorAll("[data-EFDRCfield='" + fld + "']")
    for (let e = 0; e < els.length; e++) {
      const el = els[e]
      if (EFDRC.CTRL) {
        EFDRC.placeholder(el)
      }
    }

    if (!EFDRC.CTRL) {
      for (let e = 0; e < els.length; e++) {
        els[e].setAttribute('contenteditable', 'true')
      }
    }
  }

  // image resizer
  EFDRC.registerShortcut('Shift+S', (event) => {
    EFDRC.resizeImageMode = !EFDRC.resizeImageMode
    EFDRC.maybeResizeOrClean()
  })
  EFDRC.registerShortcut('Ctrl+Shift+C', (event, el) => {
    EFDRC.wrapCloze(event, el, false)
  })
  EFDRC.registerShortcut('Ctrl+Shift+Alt+C', (event, el) => {
    EFDRC.wrapCloze(event, el, true)
  })
  EFDRC.registerShortcut('Backspace', (event, el) => {
    if (EFDRC.SPAN) event.stopPropagation()
    if (EFDRC.REMSPAN) setTimeout(() => EFDRC.removeSpan(el), 0)
  })
  EFDRC.registerShortcut('Delete', (event, el) => {
    if (EFDRC.REMSPAN) setTimeout(() => EFDRC.removeSpan(el), 0)
  })

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
