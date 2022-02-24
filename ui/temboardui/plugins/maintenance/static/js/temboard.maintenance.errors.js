function onError(xhr) {
  if (xhr.status == 401) {
    showNeedsLoginMsg();
  } else {
    alert("There was an error: " + xhr.responseJSON.error);
  }
}

function showNeedsLoginMsg() {
  if (confirm('You need to be logged in the instance agent to perform this action')) {
    var params = $.param({redirect_to: window.location.href});
    window.location.href = agentLoginUrl + '?' + params;
  }
}

/**
 * Redirects to agent login page if session is not provided
 * Should be used in each action requiring xsession authentication.
 *
 * params:
 * e - Optional browser event
 *
 */
function checkSession(e) {
  if (!xsession) {
    showNeedsLoginMsg();
    e && e.stopPropagation();
    return false;
  }
  return true;
}
