// Submit post on submit
$(document).ready(function() {
    $('#minutes').on('submit', function(event){
        create_member();
    });
});

function create_member() {
    $.ajax({
        type : "POST", // http method
        url : "minutes/", // the endpoint
        dataType: 'json',
        data : {
            'date' : $('#date').val(),
            'minute' : $('#minute').val(),
        },
        // data sent with the post request
        // handle a successful response
        success : function(data) {
            alert("Your file is uploaded");
        },
        error : function(data) {
            alert("Cannot be uploaded");
        }
    });
};
    
    
       