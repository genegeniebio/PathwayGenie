pathwayGenieApp.controller("pathwayGenieCtrl", ["$route", "ICEService", function($route, ICEService) {
	var self = this;
	self.route = $route;
	
	self.showIce = function() {
		ICEService.open();
	}
	
	self.connected = function() {
		return ICEService.connected;
	}
}]);