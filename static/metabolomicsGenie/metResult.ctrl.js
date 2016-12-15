metResultApp.controller("metResultCtrl", ["MetResultService", function(MetResultService) {
	var self = this;
	
	self.results = function() {
		return MetResultService.results;
	};
	
	self.result = function() {
		return MetResultService.result;
	};
}]);