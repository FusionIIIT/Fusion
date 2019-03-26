<<<<<<< HEAD
function editFirst(){

    var aboutSpan = $("#aboutSpan").text().trim();
    var educationSpan = $("#educationSpan").text().trim();
    var interestSpan = $("#interestSpan").text().trim();
    var contactSpan = $("#contactSpan").text().trim();


    var buttonValue = $("#editButton").val()

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

        var contactValue = $("#contactInput").val().trim();
        $("#contactSpan").text(contactValue);
        $("#contactInput").hide();
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

function editStudent() {
    var aboutSpan = $("#aboutSpan").text().trim();
    var contactSpan = $("#contactSpan").text().trim();
    var interestSpan = $("#interestSpan").text().trim();

    var buttonValue = $("#editButton").val()

    if(buttonValue == "Edit") {
        $("#editButton").val("Save");

        $("#contactInput").val(contactSpan);
        $("#contactInput").show();
        $("#contactSpan").hide();
        $("#contactIcon").hide();

        $("#aboutTextarea").val(aboutSpan);
        $("#aboutTextarea").show();
        $("#aboutSpan").hide();

        $("#interestTextarea").val(interestSpan);
        $("#interestTextarea").show();
        $("#interestSpan").hide();
    }

    else if($("#editButton").val("Save")) {
        $("#editButton").val("Edit");

        var contactValue = $("#contactInput").val().trim();
        $("#contactSpan").text(contactValue);
        $("#contactInput").hide();
        $("#contactSpan").show();
        $("#contactIcon").show();

        var aboutSpan = $("#aboutTextarea").val().trim();
        $("#aboutSpan").text(aboutSpan);
        $("#aboutTextarea").hide();
        $("#aboutSpan").show();

        var interestSpan = $("#interestTextarea").val().trim();
        $("#interestSpan").text(interestSpan);
        $("#interestTextarea").hide();
        $("#interestSpan").show();


    }
}


=======
function editFirst(){

    var aboutSpan = $("#aboutSpan").text().trim();
    var educationSpan = $("#educationSpan").text().trim();
    var interestSpan = $("#interestSpan").text().trim();
    var contactSpan = $("#contactSpan").text().trim();


    var buttonValue = $("#editButton").val()

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

        var contactValue = $("#contactInput").val().trim();
        $("#contactSpan").text(contactValue);
        $("#contactInput").hide();
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

function editStudent() {
    var aboutSpan = $("#aboutSpan").text().trim();
    var contactSpan = $("#contactSpan").text().trim();
    var interestSpan = $("#interestSpan").text().trim();

    var buttonValue = $("#editButton").val()

    if(buttonValue == "Edit") {
        $("#editButton").val("Save");

        $("#contactInput").val(contactSpan);
        $("#contactInput").show();
        $("#contactSpan").hide();
        $("#contactIcon").hide();

        $("#aboutTextarea").val(aboutSpan);
        $("#aboutTextarea").show();
        $("#aboutSpan").hide();

        $("#interestTextarea").val(interestSpan);
        $("#interestTextarea").show();
        $("#interestSpan").hide();
    }

    else if($("#editButton").val("Save")) {
        $("#editButton").val("Edit");

        var contactValue = $("#contactInput").val().trim();
        $("#contactSpan").text(contactValue);
        $("#contactInput").hide();
        $("#contactSpan").show();
        $("#contactIcon").show();

        var aboutSpan = $("#aboutTextarea").val().trim();
        $("#aboutSpan").text(aboutSpan);
        $("#aboutTextarea").hide();
        $("#aboutSpan").show();

        var interestSpan = $("#interestTextarea").val().trim();
        $("#interestSpan").text(interestSpan);
        $("#interestTextarea").hide();
        $("#interestSpan").show();


    }
}

function editCatalog() {
    var buttonValue = $("#editButton").val()
    var aboutSpan = $("#aboutSpan").text().trim();

    if(buttonValue == "Edit") {
        $("#editButton").val("Save");

        $("#aboutTextarea").val(aboutSpan);
        $("#aboutTextarea").show();
        $("#aboutSpan").hide();
    }

    else if($("#editButton").val("Save")) {
        $("#editButton").val("Edit");

        var aboutSpan = $("#aboutTextarea").val().trim();
        $("#aboutSpan").text(aboutSpan);
        $("#aboutTextarea").hide();
        $("#aboutSpan").show();
    }
}
>>>>>>> 8840ea3da5f4a670a7683a29f89c0509c75da90e
