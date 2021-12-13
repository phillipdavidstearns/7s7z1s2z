$(document).ready(function(){
	// Websocket
	var WEBSOCKET_ROUTE = "/ws";
	var ws = null;
	var ws_interval = 1000; // request status interval in ms
	var getSettings = null;

	openWebsocket();
	
	function openWebsocket(){
		if (window.location.protocol == "http:"){
			ws = new WebSocket("ws://" + window.location.host + WEBSOCKET_ROUTE);
		} else if(window.location.protocol == "https:"){
			ws = new WebSocket("wss://" + window.location.host + WEBSOCKET_ROUTE);
		};
		ws.onopen = function(evt) {
			$("#ws-status").html("Connected");
			getStatus = setInterval(getStatus, ws_interval); // get status of the MotorController on an interval
			ws.send(JSON.stringify({'get':'loadDefaults'}));
		};
		ws.onmessage = function(evt) {
			var message = null;
			try {
				message = JSON.parse(evt.data); // expecting JSON formatted messages from the MotorController
			} catch {
				console.error(error);
			};
			if (message != null){
				if ('message' in message){
					console.log(message.message);
				} else if ('status' in message){
					displayStatus(message['status']);
				};
			};
		};
		ws.onclose = function(evt) {
			$("#ws-status").html("Disconnected");
			clearInterval(getStatus); // stop trying to get the MotorController status
			ws = null;
			setTimeout(function(){openWebsocket()}, 5000); // if we get disconnected, attempt to reconnect in 5s
		};
	};

	document.getElementById('open').onclick = function () {
		ws.send(JSON.stringify({'goto':1}));
	};

	document.getElementById('closeAndPause').onclick = function () {
		ws.send(JSON.stringify({'goto':4}));
	};

	function displayStatus(status){
		for(key in status){
			id = key.concat('-status');
			try {
				if( id == "machineState-status"){
					var value = String(status[key]);
					var state = "";
					switch(value){
						case "-2":
							state = "STOPPED";
							break;
						case "-1":
							state = "PAUSED";
							break;
						case "0":
							state = "STARTUP";
							break;
						case "1":
							state = "OPENING";
							break;
						case "2":
							state = "HOLDING OPEN";
							break;
						case "3":
							state = "CLOSING";
							break;
						case "4":
							state = "HOLDING CLOSED";
							break;
						default:
							state = "N/A";
							break;
					};
					document.getElementById(id).innerHTML=state;	
				} 
			} catch (error) {
				// console.log(id);
				// console.error(error);
			};
		};
	};

	function getStatus(){
		ws.send(JSON.stringify({'get':'status'}));
	};
});