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

	//TO DO: implement SSL websockets 
	if (window.location.protocol == "http:"){
		ws = new WebSocket("ws://" + window.location.host + WEBSOCKET_ROUTE);
	} else if(window.location.protocol == "https:"){
		ws = new WebSocket("wss://" + window.location.host + WEBSOCKET_ROUTE);
	};

	if (ws != null){
		ws.onopen = function(evt) {
			$("#ws-status").html("Connected");
			getSettings = setInterval(getValenceSettings, ws_interval);
		};
		ws.onmessage = function(evt) {
			message = JSON.parse(evt.data)
			if ('message' in message){
				console.log(message['message'])
			} else {
				displayStatus(message);
			};
		};
		ws.onclose = function(evt) {
			$("#ws-status").html("Disconnected");
			clearInterval(getSettings);
		};
	};

	var mode = document.getElementById("mode");
	var sigmoid = document.getElementById("sigmoidFunction");

	document.getElementById("mode").onchange = function () {
		$("#mode-status").html(mode.value);
		console.log(mode.value);
	};

	document.getElementById('apply').onclick = function () {
		var elements = document.getElementsByTagName('input');
		var json = { 'set':{}};
		json[sigmoid.id] = sigmoid.value;
		for (var i = 0 ; i < elements.length; i++){
			json.set[elements[i].id]=elements[i].value;
		};
		data = JSON.stringify(json);
		ws.send(data);
	};

	function displayStatus(status){
		for(key in status){
			id = key.concat('-status')
			try {
				document.getElementById(id).innerHTML=String(status[key]);
			} catch (error) {
				// console.log(id);
				// console.error(error);
			};
		};
	}

	function getValenceSettings(){
		var request = {}
		request.get="all"
		ws.send(JSON.stringify(request));
	};
});