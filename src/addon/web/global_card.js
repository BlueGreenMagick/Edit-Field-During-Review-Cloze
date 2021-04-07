(function () {
  window.EFDRC = {}
  const EFDRC = window.EFDRC
  EFDRC.shortcuts = []

  const removeSpan = function (el) {
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

  const wrapCloze = function (event, el, altKey) {
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
    EFDRC.wrap('{{c' + highest + '::', '}}')
    event.preventDefault()
  }

  const ctrlLinkEnable = function () {
    const links = document.querySelectorAll('[data-EFDRCfield] a')
    for (let x = 0; x < links.length; x++) {
      const el = links[x]
      el.setAttribute('contenteditable', 'false')
    }
  }

  const ctrlLinkDisable = function () {
    const links = document.querySelectorAll("[data-EFDRCfield] a[contenteditable='false']")
    for (let x = 0; x < links.length; x++) {
      const el = links[x]
      el.removeAttribute('contenteditable')
    }
  }

  /* Handlers */

  const isInsideEfdrcDiv = function (el) {
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

  const addListener = function (handlerInfo) {
    const eventName = handlerInfo[0]
    const handler = handlerInfo[1]
    window.addEventListener(eventName, function (event) {
      const target = isInsideEfdrcDiv(event.target)
      if (target) {
        handler(event, target)
      }
    })
  }

  const handlePaste = function (e) {
    if (!EFDRC.CONF.process_paste) {
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

  const handleKeydown = function (event, target) {
    for (let i = 0; i < EFDRC.shortcuts.length; i++) {
      const scutInfo = EFDRC.shortcuts[i]
      if (matchShortcut(event, scutInfo)) {
        const handled = EFDRC.shortcuts[i].handler(event, target)
        if (handled !== -1) {
          event.preventDefault()
          event.stopPropagation()
        }
      }
    }
  }

  const handleFocus = function (event, target) {
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

  const handleBlur = function (event, target) {
    if (typeof showTooltip2 === 'function') {
      // Restore Popup Dictionary
      window.showTooltip = window.showTooltip2
      delete window.showTooltip2
      window.invokeTooltipAtSelectedElm = window.invokeTooltipAtSelectedElm2
      delete window.invokeTooltipAtSelectedElm2
    }

    const el = target
    if (EFDRC.CONF.remove_span) {
      removeSpan(el)
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

  /* Shortcuts */

  const registerShortcut = function (shortcut, handler) {
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
  EFDRC.registerShortcut = registerShortcut

  const matchShortcut = function (event, scutInfo) {
    if (scutInfo.key !== event.code.toLowerCase()) return false
    if (scutInfo.ctrl !== (event.ctrlKey || event.metaKey)) return false
    if (scutInfo.shift !== event.shiftKey) return false
    if (scutInfo.alt !== event.altKey) return false
    return true
  }

  const registerFormattingShortcut = function () {
    for (const key in EFDRC.CONF.special_formatting) {
      const format = EFDRC.CONF.special_formatting[key]
      if (!format.enabled) {
        continue
      }
      const shortcut = format.shortcut
      registerShortcut(shortcut, () => {
        if (format.arg) {
          document.execCommand(format.command, false, format.arg.value)
        } else {
          document.execCommand(format.command, false)
        }
      }) // spread args list
    }
  }

  /* Called from reviewer.py */

  EFDRC.b64DecodeUnicode = function (str) {
    return decodeURIComponent(window.atob(str).split('').map(function (c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join(''))
  }
  EFDRC.registerConfig = function (confStr) {
    EFDRC.CONF = JSON.parse(confStr)
    EFDRC.CONF.span = (EFDRC.CONF.tag === 'span')
    EFDRC.resizeImageMode = EFDRC.CONF.resize_image_default_state
  }
  EFDRC.setupReviewer = function () {
    // image resizer
    registerShortcut(EFDRC.CONF.shortcuts['image-resize'], (event) => {
      EFDRC.resizeImageMode = !EFDRC.resizeImageMode
      EFDRC.maybeResizeOrClean()
    })
    registerShortcut(EFDRC.CONF.shortcuts.cloze, (event, el) => {
      wrapCloze(event, el, false)
    })
    registerShortcut(EFDRC.CONF.shortcuts['cloze-alt'], (event, el) => {
      wrapCloze(event, el, true)
    })
    registerShortcut('Backspace', (event, el) => {
      if (EFDRC.CONF.span) return
      if (EFDRC.CONF.remove_span) setTimeout(() => removeSpan(el), 0)
      return -1
    })
    registerShortcut('Delete', (event, el) => {
      if (EFDRC.CONF.remove_span) setTimeout(() => removeSpan(el), 0)
      return -1
    })
    registerFormattingShortcut()

    const handlers = [
      ['paste', handlePaste],
      ['focusin', handleFocus],
      ['focusout', handleBlur],
      ['keydown', handleKeydown]
    ]
    for (let i = 0; i < handlers.length; i++) {
      addListener(handlers[i])
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
  }

  EFDRC.serveCard = function (fld) { // fld: string
    const els = document.querySelectorAll("[data-EFDRCfield='" + fld + "']")
    for (let e = 0; e < els.length; e++) {
      const el = els[e]
      if (EFDRC.CONF.ctrl_click) {
        const fldName = EFDRC.b64DecodeUnicode(el.getAttribute('data-EFDRCfield'))
        el.setAttribute('data-placeholder', fldName)
      }
    }

    if (!EFDRC.CONF.ctrl_click) {
      for (let e = 0; e < els.length; e++) {
        els[e].setAttribute('contenteditable', 'true')
      }
    }
  }

  EFDRC.ctrldown = function () {
    ctrlLinkEnable()
    if (EFDRC.CONF.ctrl_click) {
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
    ctrlLinkDisable()
    if (EFDRC.CONF.ctrl_click) {
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
})()
