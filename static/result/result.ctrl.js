resultApp.controller("resultCtrl", ["$scope", "ICEService", "ResultService", function($scope, ICEService, ResultService) {
	var self = this;
	
	self.pagination = {
		current: 1
	};
	
	var feat = {}

	self.connected = function() {
		return ICEService.connected
	}
	
	self.results = function() {
		return ResultService.results;
	};
	
	self.result = function() {
		if(self.results()) {
			return self.results()[self.pagination.current - 1];
		}
		else {
			return null;
		}
	}

	self.saveResults = function() {
		return ResultService.saveResults();
	};
	
	self.feature = function() {
		return feat;
	};
	
	self.setFeature = function(ft) {
		feat = ft;
	}
}]);