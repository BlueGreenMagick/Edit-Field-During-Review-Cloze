/* global autoAnswerTimeout, autoAlertTimeout, autoAgainTimeout */

// If focus in on bottom.web, ctrl key press is not catched by global_card.js
// So this code catches ctrl key presses when focus in on bottom.web

window.addEventListener('keydown', function (event) {
  if (['ControlLeft', 'MetaLeft'].includes(event.code)) {
    window.pycmd('EFDRC!ctrldown')
  }
})

window.addEventListener('keyup', function (event) {
  if (['ControlLeft', 'MetaLeft'].includes(event.code)) {
    window.pycmd('EFDRC!ctrlup')
  }
})

window.EFDRCResetTimer = function () {
  // Reset timer from Speed Focus Mode add-on.
  if (typeof autoAnswerTimeout !== 'undefined') {
    clearTimeout(autoAnswerTimeout)
  }
  if (typeof autoAlertTimeout !== 'undefined') {
    clearTimeout(autoAlertTimeout)
  }
  if (typeof autoAgainTimeout !== 'undefined') {
    clearTimeout(autoAgainTimeout)
  }
}
