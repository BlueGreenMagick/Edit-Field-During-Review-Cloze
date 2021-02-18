(function () {
  const FLD = '%(fld)s' // string
  const EFDRC = window.EFDRC // object

  const els = document.querySelectorAll("[data-EFDRCfield='" + FLD + "']")
  for (let e = 0; e < els.length; e++) {
    const el = els[e]
    EFDRC.addListeners(el, FLD)
    if (EFDRC.CTRL) {
      EFDRC.placeholder(el)
    }
  }

  if (!EFDRC.CTRL) {
    for (let e = 0; e < els.length; e++) {
      els[e].setAttribute('contenteditable', 'true')
    }
  }
})()
