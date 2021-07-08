$(document).ready(function(){
	/* Variable Reference

	Writeable:
		"sigmoidFunction" : 2,
		"mPositionOffsets" : [ 0, 0 ],
		"openDuration" : 15000,
		"openHoldDuration" : 15000,
		"closeDuration" : 12500,
		"closeHoldDuration" : 17500,
		"startupDuration" : 5000,
		"targetOpen" : 2550,
		"targetClosed" : 0,
		"powerScalar" : 2.0,
		"powerEasing" : 1.0,
		"targetWindow" : 3,
		"powerLimit" : 480,
		"powerCutoff" : 25,
		"speedCutoff" : 0.01

	Readable:
		"machineState" : 5,
		"lastMachineState" : 0,
		"target" : 0,
		"isOpen" : False,
		"isClosed" : False,
		"moveMotors" : True,
		"mPositions" : [ 0, 0 ],
		"mSpeeds" : [ 0, 0 ],
		"tCurrent" : 0,
		"tInitial" : 0,
		"tDuration" : 1,
		"tFinal" : 0
	*/
	// Websocket

	var WEBSOCKET_ROUTE = "/ws";
	var ws = null;
	var ws_interval = 2000; //sets the update interval in ms

	function openWebsocket(){

		if (window.location.protocol == "http:"){
			ws = new WebSocket("ws://" + window.location.host + WEBSOCKET_ROUTE);
		} else if(window.location.protocol == "https:"){
			ws = new WebSocket("wss://" + window.location.host + WEBSOCKET_ROUTE);
		};
		ws.onopen = function(evt) {
			$("#ws-status").html("Connected");
			getSettings = setInterval(getValenceSettings, ws_interval);
		};
		ws.onmessage = function(evt) {
			message = JSON.parse(evt.data)
			if ('message' in message){
				if (message['message'] == "Settings applied"){
					document.getElementById("apply-status").innerHTML=message['message'];
				} else {
					console.log(message['message']);
				}
			} else {
				displayStatus(message);
			};
		};
		ws.onclose = function(evt) {
			$("#ws-status").html("Disconnected");
			clearInterval(getSettings);
			ws = null
			// if we get disconnected, attempt to reconnect in 5s
			setTimeout(function(){openWebsocket()}, 5000);
		};
	};
	openWebsocket();

	// var mode = document.getElementById("mode");
	// document.getElementById("mode").onchange = function () {
	// 	$("#mode-status").html(mode.value);
	// };
	
	// document.getElementById("goto").onchange = function () {
	// 	var setState = document.getElementById("goto");
	// 	var request = {};
	// 	request.goto = setState.value;
	// 	console.log(JSON.stringify(request));
	// 	ws.send(JSON.stringify(request));
	// };

	document.getElementById('apply').onclick = function () {
		if (ws != null){
			document.getElementById("apply-status").innerHTML="Applying changes...";
			var sigmoid = document.getElementById("sigmoidFunction");
			var elements = document.getElementsByTagName('input');
			var json = { 'set':{}};
			json.set[sigmoid.id] = sigmoid.value;
			for (var i = 0 ; i < elements.length; i++){
				json.set[elements[i].id]=elements[i].value;
			};
			data = JSON.stringify(json);
			ws.send(data);
		} else {
			console.log("Websocket is disconnected. Please, wait until connection is re-established")
		};
	};

	function displayStatus(status){
		for(key in status){
			id = key.concat('-status')
			try {
				if( id == "machineState-status" ){
					var value = String(status[key]);
					var state = "";
					switch(value){
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
					};
					document.getElementById(id).innerHTML=state;	
				} else if( id == "sigmoidFunction-status" ){
					var value = String(status[key]);
					var state = "";
					switch(value){
						case "0":
							state = "Natural Log";
						break;
						case "1":
							state = "Arc Tan";
						break;
						case "2":
							state = "Sine Squared";
						break;
					};
					document.getElementById(id).innerHTML=state;	
				} else {
					document.getElementById(id).innerHTML=String(status[key]);
				};
			} catch (error) {
				// console.log(id);
				// console.error(error);
			};
		};
	};

	function getValenceSettings(){
		var request = {};
		request.get="all";
		ws.send(JSON.stringify(request));
	};
});