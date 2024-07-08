import $ from "jquery";

$("#sendEmailForm").submit(function (e) {
  e.preventDefault();
  sendEmail();
});

$("#sendSmsForm").submit(function (e) {
  e.preventDefault();
  sendSms();
});

function sendEmail() {
  clearError();
  $.ajax({
    url: "/json/test_email",
    type: "post",
    data: JSON.stringify({
      email: $("#inputTestEmail").val(),
    }),
    success: function (data) {
      var msg = "Test email successfully sent";
      msg += "\nIf the email is not received, please have a look at your SMTP server logs";
      alert(msg);
    },
    error: function (xhr) {
      console.log("error", xhr);
      showError(xhr);
    },
  });
}

function sendSms() {
  clearError();
  $.ajax({
    url: "/json/test_sms",
    type: "post",
    data: JSON.stringify({
      phone: $("#inputTestPhone").val(),
    }),
    success: function (data) {
      alert("Test SMS sent");
    },
    error: showError,
  });
}
