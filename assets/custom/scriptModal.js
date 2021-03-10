function openModal (event, record.pk) {
    var modal = $('#modal_register_edit');
    var url = $(event.target).closest('a').attr('href');
    modal.find('.modal-body').html('').load(url, function() {
        modal.modal('show');
        formAjaxSubmit(popup, url);
    });
}