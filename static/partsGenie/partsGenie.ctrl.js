partsGenieApp.controller("partsGenieCtrl", ["$scope", "ErrorService", "PartsGenieService", "PathwayGenieService", "ProgressService", "ResultService", function($scope, ErrorService, PartsGenieService, PathwayGenieService, ProgressService, ResultService) {
	var self = this;

	self.response = {"update": {"values": []}};
	self.excl_codons_regex = "([ACGTacgt]{3}(\s[ACGTacgt]{3})+)*";
	
	var jobId = null;
	
	self.restr_enzs = function() {
		return PathwayGenieService.restr_enzs();
	};
	
	self.query = PartsGenieService.query;
	
	self.submit = function() {
		reset();
		
		PathwayGenieService.submit(self.query).then(
			function(resp) {
				jobId = resp.data.job_id;
				var source = new EventSource("/progress/" + jobId);

				source.onmessage = function(event) {
					self.response = JSON.parse(event.data);
					status = self.response.update.status;
					
					if(status == "cancelled" || status == "error" || status == "finished") {
						source.close();
						
						if(status == "finished") {
							ResultService.setResults(self.response.result);
						}
					}
					
					$scope.$apply();
				};
				
				source.onerror = function(event) {
					self.response.update.status = "error";
					self.response.update.message = "Error";
					$scope.$apply();
				}
				
				ProgressService.open(self.query["app"] + " dashboard", self.cancel, self.update);
			},
			function(errResp) {
				ErrorService.open(errResp.data.message);
			});
	};
	
	self.cancel = function() {
		return PathwayGenieService.cancel(jobId);
	};
	
	self.update = function() {
		return self.response.update;
	};

	reset = function() {
		status = {"update": {"values": []}};
		error = null;
		ResultService.setResults(null);
	};
}]);