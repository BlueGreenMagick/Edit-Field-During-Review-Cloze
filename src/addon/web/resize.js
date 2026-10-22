/* global $, EFDRC */

(function () {
  // Images showing resize handles in the edited field, mapped to their copy from before the handles were added.
  // Holds images that are still loading too.
  const handledImgs = new Map()
  const resizedImgs = new WeakSet()

  const ratioShouldBePreserved = function (event) {
    if (EFDRC.CONF.resize_image_preserve_ratio === 1 && event.originalEvent.target.classList.contains('ui-resizable-se')) {
      return true
    } else if (EFDRC.CONF.resize_image_preserve_ratio === 2) {
      return true
    } else {
      return false
    }
  }

  const maybeRemoveHeight = function (img, $img, ui) {
    if (!img.naturalHeight) { return }
    const originalRatio = img.naturalWidth / img.naturalHeight
    const currentRatio = $img.width() / $img.height()
    if (Math.abs(originalRatio - currentRatio) < 0.01 || EFDRC.CONF.resize_image_preserve_ratio === 2) {
      $img.css('height', '')
      if (ui) {
        ui.element.css('height', $img.height())
      }
    }
  }

  const onDblClick = function () {
    const img = this
    resizedImgs.add(img)
    const $img = $(img)
    $img.css('width', '')
    $img.css('height', '')
    const $parents = $img.parents('div[class^=ui-]')
    $parents.css('width', '')
    $parents.css('height', '')
  }

  const showHandles = async function (img) {
    if (handledImgs.has(img)) { return }
    handledImgs.set(img, img.cloneNode())

    while (!img.complete) {
      // wait for image to load
      await new Promise(resolve => setTimeout(resolve, 20))
    }
    // Handles may have been hidden while the image was loading,
    // or set up by an earlier call that was waiting on the same image.
    if (!handledImgs.has(img) || $(img).resizable('instance') !== undefined) { return }

    const $img = $(img)
    const aspRatio = (EFDRC.CONF.resize_image_preserve_ratio === 2)
    const computedStyle = window.getComputedStyle(img)

    $img.resizable({
      start: function (event, ui) {
        if (ratioShouldBePreserved(event)) {
          // preserve ratio when using corner point to resize
          $img.resizable('option', 'aspectRatio', true).data('ui-resizable')._aspectRatio = true
        }
      },
      stop: function (event, ui) {
        $img.resizable('option', 'aspectRatio', false).data('ui-resizable')._aspectRatio = false
        if (resizedImgs.has(img)) {
          maybeRemoveHeight(img, $img, ui)
        }
      },
      resize: function (event, ui) {
        resizedImgs.add(img)
        if (ratioShouldBePreserved(event)) {
          maybeRemoveHeight(img, $img, ui)
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
    $img.css('max-width', '100%')
    $img.css('max-height', '100%')
    if (parseFloat(computedStyle.minWidth)) { // not 0
      ui.element.css('min-width', computedStyle.minWidth)
    }
    if (parseFloat(computedStyle.minHeight)) {
      ui.element.css('min-height', computedStyle.minHeight)
    }

    $img.dblclick(onDblClick)
    const $divUi = $img.parents('div[class=ui-wrapper]')
    $divUi.attr('contentEditable', 'false')
    $divUi.css('display', 'inline-block')
  }

  const hideHandles = function (img) {
    const priorImg = handledImgs.get(img)
    handledImgs.delete(img)
    // Still loading, or deleted by the user
    if ($(img).resizable('instance') === undefined || !img.isConnected) { return }

    $(img).resizable('destroy')
    // Preserve the original image unless the user resized or reset it.
    if (resizedImgs.has(img)) {
      maybeRemoveHeight(img, $(img))
      priorImg.style.width = img.style.width
      priorImg.style.height = img.style.height
    }
    img.parentNode.replaceChild(priorImg, img)
  }

  const hideAllHandles = function () {
    for (const img of handledImgs.keys()) {
      hideHandles(img)
    }
  }

  // Installed only while the field is focused, so the press that focuses the field never reaches it.
  const onFieldMouseDown = function (event) {
    // An image showing handles, or its handles
    if (event.target.closest('.ui-wrapper')) { return }
    hideAllHandles()
    if (event.target.tagName === 'IMG') {
      showHandles(event.target)
    }
  }

  // Called when the field starts being edited.
  EFDRC.setupResize = function (field) {
    if (!EFDRC.CONF.resize_image_default_state) { return }
    if (EFDRC.CONF.show_resize_on_click) {
      field.addEventListener('mousedown', onFieldMouseDown)
    } else {
      for (const img of field.querySelectorAll('img')) {
        showHandles(img)
      }
    }
  }

  // Hide handles if every image shows them, otherwise show handles on every image.
  EFDRC.toggleResize = function (field) {
    const imgs = [...field.querySelectorAll('img')]
    if (imgs.every(img => handledImgs.has(img))) {
      hideAllHandles()
    } else {
      for (const img of imgs) {
        showHandles(img)
      }
    }
  }

  // Called when the field stops being edited.
  EFDRC.cleanResize = function (field) {
    field.removeEventListener('mousedown', onFieldMouseDown)
    hideAllHandles()
  }
})()
