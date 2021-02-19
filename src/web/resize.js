/* global $, EFDRC */

(function () {
  EFDRC.resizeImageMode = EFDRC.DEFAULTRESIZE
  EFDRC.priorImgs = []

  EFDRC.prototype.savePriorImg = function (img) {
    const id = this.priorImgs.length
    this.priorImgs.push(img.cloneNode())
    img.setAttribute('data-EFDRCImgId', id)
  }

  EFDRC.prototype.restorePriorImg = function (img) {
    /*
        only save changes to width and height
        resizable img is guranteed to have the data-EFDRCImgId attribute.
        if img was added during review, resizable isn't applied to it.
        */
    const width = img.style.width
    const height = img.style.height

    // apply stored style
    const id = img.getAttribute('data-EFDRCImgId')
    const priorImg = this.priorImgs[id]
    priorImg.style.width = width
    priorImg.style.height = height

    img.parentNode.replaceChild(priorImg, img)
  }

  EFDRC.prototype.ratioShouldBePreserved = function (event) {
    if (this.preserve_ratio === 1 && event.originalEvent.target.classList.contains('ui-resizable-se')) {
      return true
    } else if (this.preserve_ratio === 2) {
      return true
    } else {
      return false
    }
  }

  EFDRC.prototype.maybeRemoveHeight = function (img, $img, ui) {
    if (!img.naturalHeight) { return }
    const originalRatio = img.naturalWidth / img.naturalHeight
    const currentRatio = $img.width() / $img.height()
    if (Math.abs(originalRatio - currentRatio) < 0.01 || this.preserve_ratio === 2) {
      $img.css('height', '')
      if (ui) {
        ui.element.css('height', $img.height())
      }
    }
  }

  EFDRC.prototype.resizeImage = async function (idx, img) {
    while (!img.complete) {
      // wait for image to load
      await new Promise(resolve => setTimeout(resolve, 20))
    }

    this.savePriorImg(img)

    const $img = $(img)
    if ($img.resizable('instance') === undefined) { // just in case?
      const aspRatio = (this.preserve_ratio === 2)
      const computedStyle = window.getComputedStyle(img)

      $img.resizable({
        start: function (event, ui) {
          if (this.ratioShouldBePreserved(event)) {
            // preserve ratio when using corner point to resize
            $img.resizable('option', 'aspectRatio', true).data('ui-resizable')._aspectRatio = true
          }
        },
        stop: function (event, ui) {
          $img.resizable('option', 'aspectRatio', false).data('ui-resizable')._aspectRatio = false
          this.maybeRemoveHeight(img, $img, ui) // this might not be working
        },
        resize: function (event, ui) {
          if (this.ratioShouldBePreserved(event)) {
            this.maybeRemoveHeight(img, $img, ui)
          }
        },
        classes: {
          // remove unneeded classes
          'ui-resizable-se': ''
        },
        minHeight: 15,
        minWidth: 15,
        aspectRatio: aspRatio
      })

      // passing maxWidth to resizable doesn't work because
      // it only takes in pixel values
      const ui = $img.resizable('instance')
      ui.element.css('max-width', computedStyle.maxWidth)
      ui.element.css('max-height', computedStyle.maxHeight)
      $img.css('max-width', '100%%') // escape percentage because string formatter
      $img.css('max-height', '100%%')
      if (parseFloat(computedStyle.minWidth)) { // not 0
        ui.element.css('min-width', computedStyle.minWidth)
      }
      if (parseFloat(computedStyle.minHeight)) {
        ui.element.css('min-height', computedStyle.minHeight)
      }

      $img.dblclick(this.onDblClick)
      const $divUi = $img.parents('div[class=ui-wrapper]')
      $divUi.attr('contentEditable', 'false')
      $divUi.css('display', 'inline-block')
    }
  }

  EFDRC.prototype.onDblClick = function () {
    const img = this
    const $img = $(img)
    $img.css('width', '')
    $img.css('height', '')
    const $parents = $img.parents('div[class^=ui-]')
    $parents.css('width', '')
    $parents.css('height', '')
  }

  EFDRC.prototype.cleanResize = function (field) {
    const resizables = field.querySelectorAll('.ui-resizable')
    for (let x = 0; x < resizables.length; x++) {
      $(resizables[x]).resizable('destroy')
    }
    const imgs = field.querySelectorAll('[data-EFDRCImgId]')
    for (let x = 0; x < imgs.length; x++) {
      this.maybeRemoveHeight(imgs[x], $(imgs[x]))
      this.restorePriorImg(imgs[x])
    }
    this.priorImgs = []
  }

  EFDRC.prototype.maybeResizeOrClean = function (focus) {
    if (focus) {
      // Called from __init__.py on field focus. Else undefined.
      this.resizeImageMode = this.DEFAULTRESIZE
    }
    if (this.resizeImageMode) {
      $(document.activeElement).find('img').each(this.resizeImage)
    } else {
      this.cleanResize(document.activeElement)
    }
  }
})()
