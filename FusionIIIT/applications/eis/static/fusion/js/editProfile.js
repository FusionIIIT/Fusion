function editFirst(){

    var aboutSpan = $("#aboutSpan").text().trim();
    var educationSpan = $("#educationSpan").text().trim();
    var interestSpan = $("#interestSpan").text().trim();
    var contactSpan = $("#contactSpan").text().trim();

    if(buttonValue == "Edit"){
        $("#editButton").val("Save");

        $("#contactInput").val(contactSpan);
        $("#contactInput").show();
        $("#contactSpan").hide();
        $("#contactIcon").hide();

        $("#aboutTextarea").val(aboutSpan);
        $("#aboutTextarea").show();
        $("#aboutSpan").hide();

        $("#educationTextarea").val(educationSpan);
        $("#educationTextarea").show();
        $("#educationSpan").hide();

        $("#interestTextarea").val(interestSpan);
        $("#interestTextarea").show();
        $("#interestSpan").hide();

    }
    else if($("#editButton").val("Save")){
        $("#editButton").val("Edit");

        console.log('after save')

        var contactValue = $("#contactInput").val().trim();
        $("#contactSpan").text(contactValue);
        $("#contactInput").hide();
        $("#ageInput").prop('disabled', false);
        //$("#ageInput").removeAttr('disabled');
        $("#contactSpan").show();
        $("#contactIcon").show();

        var aboutSpan = $("#aboutTextarea").val().trim();
        $("#aboutSpan").text(aboutSpan);
        $("#aboutTextarea").hide();
        $("#aboutSpan").show();

        var educationSpan = $("#educationTextarea").val().trim();
        $("#educationSpan").text(educationSpan);
        $("#educationTextarea").hide();
        $("#educationSpan").show();

        var interestSpan = $("#interestTextarea").val().trim();
        $("#interestSpan").text(interestSpan);
        $("#interestTextarea").hide();
        $("#interestSpan").show();

    }

}
function showModal(){
    $("#editModal")
    .modal({
    closable  : false,
    onDeny    : function(){

      return true;
    },
    onApprove : function() {
      editStudent();
    }
  }).modal('show');

}

function editStudent() {
    //$("#tinyModal").show();

    console.log('editing starts')
    $("#editButton").hide();
    $("#saveButton").show();

    $("#contactInput").show();
    $("#contactSpan").hide();
    $("#ageInput").removeAttr('disabled');

    $("#aboutTextarea").show();
    $("#aboutSpan").hide();

    $("#ageSpan").hide();
    $("#ageInput").show();

    $("#addrSpan").hide();
    $("#addrInput").show();
}