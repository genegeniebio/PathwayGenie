partsGenieApp.controller("partsGenieCtrl", ["$scope", "ErrorService", "PartsGenieService", "PathwayGenieService", "ProgressService", "ResultService", function($scope, ErrorService, PartsGenieService, PathwayGenieService, ProgressService, ResultService) {
	var self = this;
	var jobId = null;
	
	self.excl_codons_regex = "([ACGTacgt]{3}(\s[ACGTacgt]{3})+)*";
	self.query = PartsGenieService.query;
	self.response = {"update": {"values": [], "status": "waiting", "message": "Waiting..."}};

	self.restr_enzs = function() {
		return PathwayGenieService.restr_enzs();
	};

	self.submit = function() {
		jobId = null
		self.response = {"update": {"values": [], "status": "running", "message": "Submitting..."}};
		error = null;
		ResultService.setResults(null);
		
		ProgressService.open(self.query["app"] + " dashboard", self.cancel, self.update);
		
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
					source.close();
					onerror(event.message);
				}
			},
			function(errResp) {
				onerror(errResp.data.message);
			});
	};
	
	self.cancel = function() {
		return PathwayGenieService.cancel(jobId);
	};
	
	self.update = function() {
		return self.response.update;
	};
	
	onerror = function(message) {
		self.response.update.status = "error";
		self.response.update.message = "Error";
		$scope.$apply();
		ErrorService.open(message);
	};
}]);