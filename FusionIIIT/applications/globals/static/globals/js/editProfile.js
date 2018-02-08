function editFirst(){

    var aboutSpan = $("#aboutSpan").text().trim();
    var educationSpan = $("#educationSpan").text().trim();
    var interestSpan = $("#interestSpan").text().trim();
    var contactSpan = $("#contactSpan").text().trim();


    var buttonValue = $("#editButton").val();


    if(buttonValue==="Edit"){
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
    else if(buttonValue==="Save"){
        $("#editButton").val("Edit");

        var contactValue = $("#contactInput").val().trim();
        $("#contactSpan").text(contactValue);
        $("#contactInput").hide();
        $("#contactSpan").show();
        $("#contactIcon").show();

        aboutSpan = $("#aboutTextarea").val().trim();
        $("#aboutSpan").text(aboutSpan);
        $("#aboutTextarea").hide();
        $("#aboutSpan").show();

        educationSpan = $("#educationTextarea").val().trim();
        $("#educationSpan").text(educationSpan);
        $("#educationTextarea").hide();
        $("#educationSpan").show();

        interestSpan = $("#interestTextarea").val().trim();
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

        contactValue = $("#contactInput").val().trim();
        $("#contactSpan").text(contactValue);
        $("#contactInput").hide();
        $("#contactSpan").show();
        $("#contactIcon").show();

        aboutSpan = $("#aboutTextarea").val().trim();
        $("#aboutSpan").text(aboutSpan);
        $("#aboutTextarea").hide();
        $("#aboutSpan").show();

        interestSpan = $("#interestTextarea").val().trim();
        $("#interestSpan").text(interestSpan);
        $("#interestTextarea").hide();
        $("#interestSpan").show();


    }
}


function editCatalog() {
    var button =  $("#editButton");
    var buttonValue =button.val();
    var aboutSpan = $("#aboutSpan");
    var aboutSpanData = aboutSpan.text().trim();
    textbox=$("#aboutTextarea");
    textData=textbox.val().trim();
    alert('anything');


    if(buttonValue === "Edit"){
        button.val("Save");

        textbox.val(aboutSpanData);
        textbox.show();
        aboutSpan.hide();
    }

    else if(buttonValue==="Save") {
        button.val("Edit");

        $.ajax({

                url: '/spacs/convener_catalogue/',
                type: 'POST',                                               // sending POST request through ajax
                data: {
                    award_name:'Mcm',
                    catalog_content:textData,
                    csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()

                },
                success: function (response) {                              // if data added successfully
                    if(response.result==='Success'){

                    }
                    else{
                                                  // otherwise print unsuccessful message
                    }

                }
        });
        aboutSpanData = textData;
        aboutSpan.text(aboutSpanData);
        textbox.hide();
        aboutSpan.show();
    }
}
$('#select_award').on('click','.item',function (event) {
    var award_name=$(this).data('tab');


    var aboutSpan = $("#aboutSpan");
    var aboutSpanData = aboutSpan.text().trim();



    $.ajax({

                url: '/spacs/convener_catalogue/',
                type: 'GET',                                               // sending POST request through ajax
                data: {
                    award_name:award_name

                },
                success: function (response) {                              // if data added successfully
                    if(response.result==='Success'){

                        aboutSpanData=response.catalog;
                        aboutSpan.text(aboutSpanData);

                    }
                    else{
                        alert(response.result);                            // otherwise print unsuccessful message
                    }

                }
        });
});
