


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