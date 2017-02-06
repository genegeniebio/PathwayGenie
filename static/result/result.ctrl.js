resultApp.controller("resultCtrl", ["ICEService", "ResultService", function(ICEService, ResultService) {
	var self = this;
	
	self.feature = 'hello';
	
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