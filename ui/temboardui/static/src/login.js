import $ from "jquery";

function login() {
  $.ajax({
    url: "/json/login",
    type: "post",
    data: JSON.stringify({
      username: $("#inputUsername").val(),
      password: $("#inputPassword").val(),
    }),
    headers: {
      "Content-Type": "application/json",
    },
    success: function (data) {
      window.location.href = document.referrer ? document.referrer : "/";
    },
    error: function (xhr) {
      console.log("error", xhr);
      showError(xhr);
    },
  });
}

window.login = login;
