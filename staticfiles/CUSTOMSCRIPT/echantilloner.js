$("#modal-book").on("submit", ".js-book-create-form", function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          $("#book-table tbody").html(data.html_book_list);  // <-- Replace the table body
          $("#modal-book").modal("hide");  // <-- Close the modal
        }
        else {
          $("#modal-book .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  });