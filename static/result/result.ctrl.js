resultApp.controller("resultCtrl", ["$http", "ICEService", "ResultService", function($http, ICEService, ResultService) {
	var self = this;
	
	self.connected = function() {
		return ICEService.connected
	}
	
	self.results = function() {
		return ResultService.results;
	};
	
	self.result = function() {
		return ResultService.result;
	};

	self.saveResults = function() {
		return ResultService.saveResults();
	};
}]);