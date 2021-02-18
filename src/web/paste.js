// updated last at 2020 Feb 20
// from qt.ts.src.editor.ts
(function () {
  'use strict'

  const parseHTML = function (str) {
    const tmp = document.implementation.createHTMLDocument()
    tmp.body.innerHTML = str
    return tmp.body.children
  }
  const filterHTML = function (html, internal, extendedMode) {
    // wrap it in <top> as we aren't allowed to change top level elements
    const top = parseHTML('<ankitop>' + html + '</ankitop>')[0]
    if (internal) {
      filterInternalNode(top)
    } else {
      filterNode(top, extendedMode)
    }
    let outHtml = top.innerHTML
    if (!extendedMode && !internal) {
      // collapse whitespace
      outHtml = outHtml.replace(/[\n\t ]+/g, ' ')
    }
    outHtml = outHtml.trim()
    // console.log(`input html: ${html}`);
    // console.log(`outpt html: ${outHtml}`);
    return outHtml
  }

  const allowedTagsBasic = {}
  const allowedTagsExtended = {}

  let TAGS_WITHOUT_ATTRS = ['P', 'DIV', 'BR', 'SUB', 'SUP']
  for (const tag of TAGS_WITHOUT_ATTRS) {
    allowedTagsBasic[tag] = { attrs: [] }
  }

  TAGS_WITHOUT_ATTRS = [
    'H1',
    'H2',
    'H3',
    'I',
    'LI',
    'UL',
    'OL',
    'BLOCKQUOTE',
    'CODE',
    'PRE',
    'RP',
    'RT',
    'RUBY',
    'STRONG',
    'TABLE',
    'DD',
    'DT',
    'DL',
    'B',
    'U',
    'I',
    'RUBY',
    'RT',
    'RP',
    'UL'
  ]
  for (const tag of TAGS_WITHOUT_ATTRS) {
    allowedTagsExtended[tag] = { attrs: [] }
  }

  allowedTagsBasic.IMG = { attrs: ['SRC'] }

  allowedTagsExtended.A = { attrs: ['HREF'] }
  allowedTagsExtended.TR = { attrs: ['ROWSPAN'] }
  allowedTagsExtended.TD = { attrs: ['COLSPAN', 'ROWSPAN'] }
  allowedTagsExtended.TH = { attrs: ['COLSPAN', 'ROWSPAN'] }
  allowedTagsExtended.FONT = { attrs: ['COLOR'] }

  const allowedStyling = {
    color: true,
    'background-color': true,
    'font-weight': true,
    'font-style': true,
    'text-decoration-line': true
  }

  const isNightMode = function () {
    return document.body.classList.contains('nightMode')
  }

  const filterExternalSpan = function (node) {
    // filter out attributes
    let toRemove = []
    for (const attr of node.attributes) {
      const attrName = attr.name.toUpperCase()
      if (attrName !== 'STYLE') {
        toRemove.push(attr)
      }
    }
    for (const attributeToRemove of toRemove) {
      node.removeAttributeNode(attributeToRemove)
    }
    // filter styling
    toRemove = []
    for (const name of node.style) {
      if (!Object.prototype.hasOwnProperty.call(allowedStyling, name)) {
        toRemove.push(name)
      }
      if (name === 'background-color' && node.style[name] === 'transparent') {
        // google docs adds this unnecessarily
        toRemove.push(name)
      }
      if (isNightMode()) {
        // ignore coloured text in night mode for now
        if (name === 'background-color' || name === 'color') {
          toRemove.push(name)
        }
      }
    }
    for (const name of toRemove) {
      node.style.removeProperty(name)
    }
  }

  allowedTagsExtended.SPAN = filterExternalSpan

  // add basic tags to extended
  Object.assign(allowedTagsExtended, allowedTagsBasic)

  // filtering from another field
  const filterInternalNode = function (node) {
    if (node.style) {
      node.style.removeProperty('background-color')
      node.style.removeProperty('font-size')
      node.style.removeProperty('font-family')
    }
    // recurse
    for (const child of node.childNodes) {
      filterInternalNode(child)
    }
  }

  // filtering from external sources
  const filterNode = function (node, extendedMode) {
    // text node?
    if (node.nodeType === 3) {
      return
    }

    // descend first, and take a copy of the child nodes as the loop will skip
    // elements due to node modifications otherwise

    const nodes = []
    for (const child of node.childNodes) {
      nodes.push(child)
    }
    for (const child of nodes) {
      filterNode(child, extendedMode)
    }

    if (node.tagName === 'ANKITOP') {
      return
    }

    let tag
    if (extendedMode) {
      tag = allowedTagsExtended[node.tagName]
    } else {
      tag = allowedTagsBasic[node.tagName]
    }
    if (!tag) {
      if (!node.innerHTML || node.tagName === 'TITLE') {
        node.parentNode.removeChild(node)
      } else {
        node.outerHTML = node.innerHTML
      }
    } else {
      if (typeof tag === 'function') {
        // filtering function provided
        tag(node)
      } else {
        // allowed, filter out attributes
        const toRemove = []
        for (const attr of node.attributes) {
          const attrName = attr.name.toUpperCase()
          if (tag.attrs.indexOf(attrName) === -1) {
            toRemove.push(attr)
          }
        }
        for (const attributeToRemove of toRemove) {
          node.removeAttributeNode(attributeToRemove)
        }
      }
    }
  }

  window.pasteHTML = function (html, internal) {
    try {
      html = filterHTML(html, internal, false)
    } finally {
      document.execCommand('inserthtml', false, html)
    }
  }
})()
