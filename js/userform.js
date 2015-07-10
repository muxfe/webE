$(function() {

    $("input,textarea").jqBootstrapValidation({
        preventSubmit: true,
        submitError: function($form, event, errors) {
            // additional error messages or events
        },
        submitSuccess: function($form, event) {
            // Prevent spam click and default submit behaviour
            $("#btnSubmit").attr("disabled", true);
            event.preventDefault();
            
            // get values from FORM
            var username = $("input#username").val();
            var password = $("input#password").val();

            var url = $("#userForm").attr("name") + ".html";
            
            $.ajax({
                url: url,
                type: "POST",
                data: {
                    username: username,
                    password: password,
                },
                cache: false,
                success: function() {
                    // Enable button & show success message
                    $('#success').html("<div class='alert alert-success'>");
                    $('#success > .alert-success').html("<button type='button' class='close' data-dismiss='alert' aria-hidden='true'>&times;")
                        .append("</button>");
                    $('#success > .alert-success')
                        .append("<strong>登录成功！</strong>");
                    $('#success > .alert-success')
                        .append('</div>');

                    setTimeout('window.location = "index.html"', 1000);
                },
                error: function() {
                    // Fail message
                    $('#success').html("<div class='alert alert-danger'>");
                    $('#success > .alert-danger').html("<button type='button' class='close' data-dismiss='alert' aria-hidden='true'>&times;")
                        .append("</button>");
                    $('#success > .alert-danger').append("<strong>登录失败!</strong>");
                    $('#success > .alert-danger').append('</div>');
                    //clear all fields
                    $('#userForm').trigger("reset");
                },
            })
        },
        filter: function() {
            return $(this).is(":visible");
        },
    });

    $("a[data-toggle=\"tab\"]").click(function(e) {
        e.preventDefault();
        $(this).tab("show");
    });
});

// When clicking on Full hide fail/success boxes
$('#name').focus(function() {
    $('#success').html('');
});
