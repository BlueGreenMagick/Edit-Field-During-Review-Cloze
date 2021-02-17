/*
    If focus in on bottom.web, ctrl key press is not catched by global_card.js
    So this code catches ctrl key presses when focus in on bottom.web
*/
(function () {
  if (typeof EFDRConctrlkey !== 'function') {
    window.EFDRConctrlkey = function () {
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
    }
    window.EFDRConctrlkey()
  }
})()
