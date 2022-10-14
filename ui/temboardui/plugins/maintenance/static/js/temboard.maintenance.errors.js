function onError(xhr) {
  if (xhr.status == 401) {
    showNeedsLoginMsg();
  } else {
    showError(xhr)
  }
}

function showNeedsLoginMsg() {
  if (confirm('You need to be logged in the instance agent to perform this action')) {
    var params = $.param({redirect_to: window.location.href});
    window.location.href = agentLoginUrl + '?' + params;
  }
}
