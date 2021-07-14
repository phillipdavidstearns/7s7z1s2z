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
			getSettings = setInterval(getValenceSettings, ws_interval); // get status of the MotorController on an interval
			ws.send(JSON.stringify({'get':'loadDefaults'}));
		};
		ws.onmessage = function(evt) {
			var message = null;
			try{
				message = JSON.parse(evt.data); // expecting JSON formatted messages from the MotorController
			} catch{
				console.error(error);
			};
			if (message != null){
				if ('message' in message){
					console.log(message.message);
				} else if ('settings' in message){
					if(message['settings']=="applied"){
						document.getElementById("apply-status").innerHTML=" Settings applied.";
					} else {
						console.log(message.settings);
					};
				} else if('errors' in message){
					console.log(message['errors']);
					document.getElementById("apply-status").innerHTML=" Errors applying settings. See Console for details.";	
				} else if('status' in message){
					displayStatus(message['status']);
				} else if('load' in message){
					loadValues(message['load']);
				};
			};
		};
		ws.onclose = function(evt) {
			$("#ws-status").html("Disconnected");
			clearInterval(getSettings); // stop trying to get the MotorController status
			ws = null;
			setTimeout(function(){openWebsocket()}, 5000); // if we get disconnected, attempt to reconnect in 5s
		};
	};

	document.getElementById('open').onclick = function () {
		ws.send(JSON.stringify({'goto':1}));
	};

	document.getElementById('close').onclick = function () {
		ws.send(JSON.stringify({'goto':3}));
	};

	document.getElementById('pause').onclick = function () {
		ws.send(JSON.stringify({'set':'pause'}));
	};

	document.getElementById('resume').onclick = function () {
		ws.send(JSON.stringify({'set':'resume'}));
	};

	document.getElementById('loadSettings').onclick = function () {
		ws.send(JSON.stringify({'get':'loadSettings'}));
	};

	document.getElementById('loadDefaults').onclick = function () {
		ws.send(JSON.stringify({'get':'loadDefaults'}));
	};

	document.getElementById('saveSettings').onclick = function () {
		ws.send(JSON.stringify({'set':'saveSettings'}));
	};

	document.getElementById('saveDefaults').onclick = function () {
		ws.send(JSON.stringify({'set':'saveDefaults'}));
	};

	// document.getElementById("m1Flipped").onchange = function (){
	// 	var request = { 'set':{}};
	// 	request.set['m1Flipped'] = document.getElementById("m1Flipped").checked;
	// 	ws.send(JSON.stringify(request));
	// }

	// document.getElementById("m2Flipped").onchange = function (){
	// 	var request = { 'set':{}};
	// 	request.set['m2Flipped'] = document.getElementById("m2Flipped").checked;
	// 	ws.send(JSON.stringify(request));
	// }
	
	document.getElementById('apply').onclick = function () {
		if (ws != null){
			var request = { 'set':{}};
			document.getElementById("apply-status").innerHTML="Applying changes...";
			var sigmoid = document.getElementById("sigmoidFunction");
			request.set[sigmoid.id] = sigmoid.value;
			var elements = document.getElementsByTagName('input');
			for (var i = 0 ; i < elements.length; i++){
				if(elements[i].id == "m1Flipped" || elements[i].id == "m2Flipped"){
					request.set[elements[i].id] = elements[i].checked;
				} else {
					request.set[elements[i].id]=elements[i].value;
				};
			};
			ws.send(JSON.stringify(request));
		} else {
			console.log("Websocket is disconnected. Please, wait until connection is re-established")
		};
	};

	function loadValues(values){
		for(id in values){
			try {
				var element = document.getElementById(id)
				if (id == "m1Flipped" && values[id] != element.checked ){
					element.click();
				} else if (id == "m2Flipped" && values[id] != element.checked){
					element.click();
				} else {
					element.value=values[id];
				};
			} catch (error) {
				// console.log(id);
				console.error(error);
			};
		};
	};

	function displayStatus(status){
		for(key in status){
			id = key.concat('-status');
			try {
				if( id == "machineState-status" || id == "lastMachineState-status"){
					var value = String(status[key]);
					var state = "";
					switch(value){
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
							state=value;
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
		ws.send(JSON.stringify({'get':'status'}));
	};
});