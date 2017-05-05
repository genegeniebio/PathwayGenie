iceApp.factory("ICEService", ["$http", "$rootScope", "$uibModal", function($http, $rootScope, $uibModal) {
	var obj = {};
	obj.ice = {'url': 'https://ice.synbiochem.co.uk',
				'username': null,
				'password': null,
				'groups': null};

	obj.connected = false;
	
	obj.open = function() {
		$uibModal.open({
			animation: true,
			ariaLabelledBy: 'modal-title',
			ariaDescribedBy: 'modal-body',
			templateUrl: '/static/ice/ice.html',
			controller: 'iceInstanceCtrl',
			controllerAs: 'ctrl',
		});
	}
	
	obj.connect = function() {
		$http.post("/ice/connect", {'ice': obj.ice}).then(
				function(resp) {
					obj.connected = resp.data.connected;
				},
				function(errResp) {
					obj.connected = false;
				});
	}
	
	obj.disconnect = function() {
		obj.ice.username = null;
		obj.ice.password = null;
		obj.ice.groups = null;
		obj.connected = false;
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