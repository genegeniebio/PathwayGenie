resultApp.controller("resultCtrl", ["ICEService", "ResultService", function(ICEService, ResultService) {
	var self = this;
	
	self.feat = {'name': 'harold', 'desc': 'something', 'forward': true}

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
	
	self.feature = function() {
		return self.feat;
	};
	
	self.setFeature = function(ft) {
		// self.feat = {'name': 'jim', 'desc': 'hello', 'forward': false};
		self.feat = ft;
	}
}]);