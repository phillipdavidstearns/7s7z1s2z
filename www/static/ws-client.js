$(document).ready(function(){

	// Websocket

	var WEBSOCKET_ROUTE = "/ws";
	var ws = null;
	var ws_interval = 1000; //sets the update interval in ms

	//TO DO: implement SSL websockets 
	if(window.location.protocol == "http:"){
		ws = new WebSocket("ws://" + window.location.host + WEBSOCKET_ROUTE);
	} else if(window.location.protocol == "https:"){
		ws = new WebSocket("wss://" + window.location.host + WEBSOCKET_ROUTE);
	}

	ws.onopen = function(evt) {
		$("#ws-status").html("Connected");
		getSettings = setInterval(getValenceSettings, ws_interval);
	};

	ws.onmessage = function(evt) {
		displaySettings();
	};

	ws.onclose = function(evt) {
		$("#ws-status").html("Disconnected");
		//clears any possible intervals that might be running
		clearInterval(getSettings);
	};

	// JSON.stringify()
	// JSON.parse()

	var joy1IinputPosX = document.getElementById("joy1PosX");
	var joy1InputPosY = document.getElementById("joy1PosY");
	var joy1Dir = document.getElementById("joy1Dir");
	var joy1X = document.getElementById("joy1X");
	var joy1Y = document.getElementById("joy1Y");


	function getValenceSettings(){
		ws.send("get settings");
	}

	function applySettings(){
		ws.send("apply settings");
	}

	function displaySettings(){	
		machineS.value=Joy1.GetPosX();
		joy1InputPosY.value=Joy1.GetPosY();
		joy1Dir.value=Joy1.GetDir();
		joy1X.value=Joy1.GetX();
		joy1Y.value=Joy1.GetY();
	}

	// Buttons not currently being used

	$("#green_on").click(function(){
		ws.send("on_g");
	});

	$("#green_off").click(function(){
		ws.send("off_g");
	});

	$("#red_on").click(function(){
		ws.send("on_r");
	});

	$("#red_off").click(function(){
		ws.send("off_r");
	});

	$("#blue_on").click(function(){
		ws.send("on_b");
	});

	$("#blue_off").click(function(){
		ws.send("off_b");
	});

	$("#white_on").click(function(){
		ws.send("on_w");
	});

	$("#white_off").click(function(){
		ws.send("off_w");
	});
});
