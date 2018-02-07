resultApp.controller("resultCtrl", ["$scope", "ICEService", "ResultService", function($scope, ICEService, ResultService) {
	var self = this;
	
	self.pagination = {
		current: 1
	};
	
	var selected = {}

	self.connected = function() {
		return ICEService.connected
	}
	
	self.results = function() {
		return ResultService.results;
	};
	
	self.results_saved = function() {
		return ResultService.results_saved();
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
	
	self.selected = function() {
		return selected;
	};
	
	self.toggleSelected = function(ft) {
		if(selected === ft) {
			selected = self.result();
		}
		else {
			selected = ft;
		}
	}
	
	$scope.$watch(function() {
		return self.result();
	},               
	function(result) {
		self.toggleSelected(result);
	}, true);
}]);