iceApp.controller("iceInstanceCtrl", ["$uibModalInstance", "ICEService", function($uibModalInstance, ICEService) {
	var self = this;
	
	self.ice = function() {
		return ICEService.ice;
	};
	
	self.connected = function() {
		return ICEService.connected;
	}
	
	self.connecting = function() {
		return ICEService.connecting;
	}
	
	self.error = function() {
		return ICEService.error;
	}
	
	self.connect = function() {
		return ICEService.connect();
	}
	
	self.disconnect = function() {
		return ICEService.disconnect();
	}
	
	self.close = function() {
		$uibModalInstance.close();
	};
}]);