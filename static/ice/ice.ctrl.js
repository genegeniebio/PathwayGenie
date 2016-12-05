iceApp.controller("iceCtrl", ["ICEService", function(ICEService) {
	var self = this;
	
	self.ice = function() {
		return ICEService.ice;
	};
	
	self.connected = function() {
		return ICEService.connected;
	}
	
	self.connect = function() {
		return ICEService.connect();
	}
}]);