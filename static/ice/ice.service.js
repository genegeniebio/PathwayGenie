iceApp.factory("ICEService", ["$http", "ErrorService", function($http, ErrorService) {
	var obj = {};
	obj.ice = {'url': null, 'username': null, 'password': null};
	obj.connected = false;
	
	obj.connect = function() {
		$http.post("/ice/connect", {'ice': obj.ice}).then(
				function(resp) {
					obj.connected = true;
				},
				function(errResp) {
					obj.connected = false;
					ErrorService.open(errResp.data.message);
				});
	}
	
	return obj;
}]);