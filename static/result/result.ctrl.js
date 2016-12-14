resultApp.controller("resultCtrl", ["$http", "ICEService", "ResultService", function($http, ICEService, ResultService) {
	var self = this;
	
	self.feature = 'hello';
	
	self.setFeature = function(f) {
		self.feature = f;
	}
	
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