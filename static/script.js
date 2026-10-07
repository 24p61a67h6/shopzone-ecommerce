// ==========================================================
// SHOPZONE JAVASCRIPT
// ==========================================================


// Automatically hide flash messages

setTimeout(function () {

    const messages = document.querySelectorAll(".flash");

    messages.forEach(function (message) {

        message.style.opacity = "0";

        setTimeout(function () {
            message.remove();
        }, 500);

    });

}, 3500);


// Confirm delete actions

document.addEventListener("DOMContentLoaded", function () {

    const deleteButtons =
        document.querySelectorAll(".delete-btn");

    deleteButtons.forEach(function (button) {

        button.addEventListener("click", function (event) {

            if (!confirm("Are you sure you want to delete this?")) {
                event.preventDefault();
            }

        });

    });

});