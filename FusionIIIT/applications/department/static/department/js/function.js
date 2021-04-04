$(document).ready(function(){
    console.log("TTTTTTTT");
  });
  
  
  
function announce(event)
        {
        var message= $('input[name="announcement"]').val();
        var batch = $('input[name="batch"]').val();
        var programme =  $('input[name="programme"]').val() ;
        var department = $('input[name="department"]').val() ;
        var upload_announcement =$('input[name="upload_announcement"]').val() ;
        console.log(batch);
        console.log(message);
        console.log(programme);
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
                window.location.replace('http://localhost:8000/dep/file_request/');
            }, 1500);

                    
                },
                error : function (data,err){
                    alert('Announcement successfully made ... ');

                }
            });
        }
    };

    function request(event)
    {
    var department= $('input[name="Department"]').val();
    var location = $('input[name="Location"]').val();
    var request_details =  $('input[name="request_details"]').val() ;
    var upload_request=$('input[name="upload_request"]').val() ;
    console.log(department);
    console.log(location);
    console.log(request_details);
    if(department=="" || location=="" || request_details =="" )
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
                'department' : department,
                'location' : location,
                'request_details' : request_details,
                'upload_request' : upload_request,
            },
            success : function (data){

                alert("Request successfully made!!");
                setTimeout(function() {
            window.location.replace('http://localhost:8000/dep/file_request/');
        }, 1500);

            },
            error : function (data,err){
                alert('Request successfully made ... ');

            }
        });
    }
};

