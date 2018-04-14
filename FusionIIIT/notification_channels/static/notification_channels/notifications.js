function wsstart(){
	notif_socket = new WebSocket("ws://"+window.location.host+"/notifications/");
	
	notif_socket.onmessage = function(event){
	var data = JSON.parse(event.data);
	console.log(data);
	}
	
	notif_socket.onopen = function(event){
		console.log("connected to notification_channels.");
	}
	notif_socket.onclose = warning;
}

function warning(){
	console.log("Connection error while connecting to notification_channels.");
	setTimeout(wsstart, 10000);
}

wsstart();


$(document).ready(function(){
	const notif_button = $(".notification-button");
	const notif_div = $(".notification-div");

	function reloadNotifications(event){
		$.ajax({
			type: "GET",
			url: "/notifications/type-sorted-notifs/",
			success:function(data){
				notif_div.html(data);
			},
			error:function(data){
				console.log(data);
			},
		});
	}

	notif_button.click(reloadNotifications);

	$(document).on("click", "a.type-sorted-div", function(event){
		const url = "/notifications/seen-all/"+$(this).attr("data-tab")+"/";
		$.ajax({
			type: "GET",
			url: url,
			success:function(data){
				// console.log("success",data);
			},
			error:function(data){
				console.log("error",data)
			},
		});
	});

	$(document).on("click", "a.read-all", function(event){
		const url = "/notifications/read-all/"+$(this).attr("data")+"/";
		$.ajax({
			type: "GET",
			url: url,
			success:function(data){
				// console.log("success",data);
				reloadNotifications();
			},
			error:function(data){
				console.log("error",data)
			},
		});
	});
});