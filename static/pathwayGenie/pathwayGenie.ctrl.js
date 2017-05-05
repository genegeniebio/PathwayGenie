pathwayGenieApp.controller("pathwayGenieCtrl", ["ICEService", function(ICEService) {
	var self = this;
	
	self.showIce = function() {
		ICEService.open();
	}
	
	self.connected = function() {
		return ICEService.connected;
	}
}]);