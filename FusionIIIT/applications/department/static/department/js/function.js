$(document).ready(function(){
    console.log("TTTTTTTT");
  });
  
  
  
function announce(event)
        {
        var message= $('input[name="announcement"]').val();
        var batch = $('input[name="batch"]').val();
        var programme =  $('input[name="programme"]').val() ;
        var upload_announcement =$('input[name="upload_announcement"]').val() ;
        // console.log(batch);
        // console.log(message);
        // console.log(programme);
        if(message=="" || batch=="" || programme =="" )
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

