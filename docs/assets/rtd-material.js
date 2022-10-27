document.addEventListener('readystatechange', function() {
  if ('complete' != document.readyState) {
    return
  }

  var rtd = document.querySelector('div.injected')
  if (null !== rtd) {
    rtd.remove()
  }
})
