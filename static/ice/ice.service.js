iceApp.factory("ICEService", ["$http", "$rootScope", "$uibModal", function($http, $rootScope, $uibModal) {
	var obj = {};
	obj.ice = {'url': 'https://ice.synbiochem.co.uk',
			'username': null,
			'password': null,
			'groups': null};

	obj.status = "DISCONNECTED";
	obj.message = null;

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
		obj.status = "CONNECTING";
		obj.message = "Connecting...";

		$http.post("/ice/connect", {'ice': obj.ice}).then(
				function(resp) {
					obj.connected = resp.data.connected;
					obj.connecting = false;
					obj.status = "CONNECTED";
					obj.message = "Connected";
				},
				function(errResp) {
					obj.connected = false;
					obj.connecting = false;
					obj.status = "ERROR";
					obj.message = errResp.data.message;
				});
	}

	obj.disconnect = function() {
		obj.ice.username = null;
		obj.ice.password = null;
		obj.ice.groups = null;
		obj.status = "DISCONNECTED";
		obj.message = null;
	}

	return obj;
}]);