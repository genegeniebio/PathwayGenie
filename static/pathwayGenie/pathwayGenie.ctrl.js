pathwayGenieApp.controller("pathwayGenieCtrl", ["$route", "ICEService", function($route, ICEService) {
	var self = this;
	self.route = $route;
	
	self.connected = function() {
		return ICEService.connected;
	}
}]);