pathwayGenieApp.controller("pathwayGenieCtrl", ["ICEService", "PathwayGenieService", function(ICEService, PathwayGenieService) {
	var self = this;
	
	self.showIce = function() {
		ICEService.open();
	}
	
	self.connected = function() {
		return ICEService.connected;
	}
	
	self.toggleHelp = function() {
		return PathwayGenieService.toggleHelp();
	}
}]);