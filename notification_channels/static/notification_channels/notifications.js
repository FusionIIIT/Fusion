function wsstart(){
	notif_socket = new WebSocket("ws://"+window.location.host+"/notifications/");
	
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
	const notif_label = $(".notification-label");

	function attachMenu(event){
			const notif_menu = $(".notification-menu");
			const notif_tabs = $(".notification-tabs");
			notif_menu.on('click', '.item', function() {
		    if(!$(this).hasClass('dropdown')) {
		        $(this)
		          .addClass('active')
		          .siblings('.item')
		            .removeClass('active');
		      }
		    const tab_segment = $(this).attr('data-tab');
		    const tab = notif_tabs.find("[data-tab="+tab_segment+"]").each(function(event){
		        $(this)
		          .addClass('active')
		          .siblings('.tab')
		            .removeClass('active');
		    });
		    
		    });
	}
	
	function updateNotificationLabel(event){
		$.ajax({
			type: "GET",
			url: "/notifications/get-unseen-count/",
			success:function(data){
				notif_label.text(data.count);
				if(parseInt(data.count)>0){
					notif_label.show();
				}
				else{
					notif_label.hide();
				}
			},
			error:function(data){
				console.log(data);
			},
		});
	}

	notif_socket.onmessage = function(event){
			var data = JSON.parse(event.data);
			updateNotificationLabel();
			Lobibox.notify('info',{
				title: data.title,
				msg: data.message,
				onClickUrl: data.url,
			});
		}

	updateNotificationLabel()

	function reloadNotifications(event){
		$.ajax({
			type: "GET",
			url: "/notifications/type-sorted-notifs/",
			success:function(data){
				notif_div.html(data);
				attachMenu();
				typeLabelUpdate();
			},
			error:function(data){
				console.log(data);
			},
		});
	}

	function typeLabelUpdate(event){
		$(".type-label").each(function(event){
			const notif_label = $(this);
			const data = parseInt(notif_label.text());
			if(data>0){
				notif_label.show();
			}
			else{
				notif_label.hide();
			}
		});
	}

	notif_button.click(reloadNotifications);

	$(document).on("click", "a.type-sorted-div", function(event){
		const url = "/notifications/seen-all/";
		const notif_type = $(this).attr("data-tab");
		$.ajax({
			type: "GET",
			url: url,
			data: { "type": notif_type },
			success:function(data){
				// console.log("success",data);
				updateNotificationLabel();
				$("."+notif_type+"-notification-label").hide();
			},
			error:function(data){
				console.log("error",data)
			},
		});
	});


	$(document).on("click", "a.read-all", function(event){
		const url = "/notifications/read-all/";
		const item = $(this);
		$.ajax({
			type: "GET",
			url: url,
			data: { "type": item.attr("data") },
			success:function(data){
				// console.log("success",data);
				reloadNotifications();
				updateNotificationLabel();		
			},
			error:function(data){
				console.log("error",data)
			},
		});
	});


	function mark_read(url){
		$.ajax({
			type: "GET",
			url: url,
			success:function(data){
				console.log("success",data);	
			},
			error:function(data){
				console.log("error",data)
			},
		});
	}
	

	$(document).on("click", "a.notification-anchor", function(event){
		const url = "/notifications/read/"+$(this).attr("data")+"/";
		const item = $(this);
		mark_read(url);
		const redirect_url = item.attr("href");
		if(redirect_url!="#"){
			window.location = window.location.hostname + redirect_url;
		}

	});


});