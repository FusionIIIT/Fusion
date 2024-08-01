$(document).ready(function(){
    console.log("TTTTTTTT");
  });
  
  
  
function announce(event)
    {
    var message= $('input[name="announcement"]').val();
    var batch = $('input[name="batch"]').val();
    var programme =  $('input[name="programme"]').val();
    var department = $('input[name="department"]').val();
    var upload_announcement =$('input[name="upload_announcement"]').val();
    if(message=="" || batch=="" || programme =="" || department=="")
    {
        alert("Please fill all the details!");
        return;
    }
    else
    {
        event.preventDefault();
        $.ajax({
            type : 'POST',
            url : '.',
            data : {
                'message' : message,
                'batch' : batch,
                'programme' : programme,
                'upload_announcement' : upload_announcement,
                'department' : department,
            },
            success : function (data){

                alert("Announcement successfully made!!");
                setTimeout(function() {
                    window.location.reload();
                }, 1500);

                
            },
            error : function (data,err){
                alert('Announcement successfully made ... ');

            }
        });
    }
};

function updateDepartment(event) {
    var email = $('input[name="email"]').val();
    var contactNumber = $('input[name="contact_number"]').val();
    var facilities = $('textarea[name="facilities"]').val();
    var labs = $('textarea[name="labs"]').val();

    if (email === "" || contactNumber === "" || facilities === "" || labs === "" || departmentId === "") {
        alert("Please fill all the details!");
        return;
    } else {
        event.preventDefault();
        $.ajax({
            type: 'POST',
            url: '.',  // Specify the URL to your view for updating department information
            data: {
                'email': email,
                'contact_number': contactNumber,
                'facilities': facilities,
                'labs': labs,
            },
            success: function(data) {
                alert("Department information updated successfully!");
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            },
            error: function(data, err) {
                alert('Failed to update department information.');
            }
        });
    }
}

function request(event)
    {
    var request_type= $('input[name="request_type"]').val();
    var request_to = $('input[name="request_to"]').val();
    var request_details =  $('input[name="request_details"]').val();

    if(request_type=="" || request_to=="" || request_details =="" )
    {
        alert("Please fill all the details!");
        return;
    }
    else
    {
        event.preventDefault();
        $.ajax({
            type : 'POST',
            url : '.',
            data : {
                'request_type' : request_type,
                'request_to' : request_to,
                'request_details' : request_details,
            },
            success : function (data){

                alert("Request successfully made!!");
                setTimeout(function() {
            window.location.reload();
        }, 1500);

            },
            error : function (data,err){
                alert('Request successfully made ... ');

            }
        });
    }
};

function editStatus(event){
    alert("working but dont know what to do");
};

