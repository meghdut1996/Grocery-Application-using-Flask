$(function () {
    $('.js-sweetalert button').on('click', function () {
        var type = $(this).data('type');
        var id = $(this).val();
        if (type === 'confirm') {
            showConfirmMessage(id);
        }
    });
});

function showConfirmMessage(id) {
    swal({
        title: "Are you sure?",
        text: "You will not be able to recover this Product!",
        type: "warning",
        showCancelButton: true,
        confirmButtonColor: "#DD6B55",
        confirmButtonText: "Yes, delete it!",
        closeOnConfirm: false
    }, function () {
        var form=document.createElement("form");
        form.method="POST";
        form.action="/delete_product/" +id;
        document.body.appendChild(form);
        form.submit();
        swal("Deleted!", "Your product has been Deleted", "success");
    });
}