iceApp.factory("ICEService", ["$http", "$rootScope","ErrorService", function($http, $rootScope, ErrorService) {
	var obj = {};
	obj.ice = {'url': 'https://ice.synbiochem.co.uk',
				'username': null,
				'password': null};

	obj.connected = false;
	
	obj.connect = function() {
		$http.post("/ice/connect", {'ice': obj.ice}).then(
				function(resp) {
					obj.connected = resp.data.connected;
				},
				function(errResp) {
					obj.connected = false;
				});
	}
	
	$rootScope.$watch(function() {
		return obj.ice;
	},               
	function(values) {
		if(obj.connected) {
			obj.connect();
		}
	}, true);
	
	return obj;
}]);