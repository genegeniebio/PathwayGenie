partsGenieApp.controller("partsGenieCtrl", ["$scope", "ErrorService", "PartsGenieService", "PathwayGenieService", "ProgressService", "ResultService", function($scope, ErrorService, PartsGenieService, PathwayGenieService, ProgressService, ResultService) {
	var self = this;
	var jobId = null;
	
	self.excl_codons_regex = "([ACGTacgt]{3}(\s[ACGTacgt]{3})+)*";
	self.submitting = false;
	self.query = PartsGenieService.query;
	self.response = {"update": {"values": [], "message": "Submitting..."}};

	self.restr_enzs = function() {
		return PathwayGenieService.restr_enzs();
	};

	self.submit = function() {
		self.submitting = true;
		jobId = null
		self.response = {"update": {"values": [], "message": "Submitting..."}};
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
						
						self.submitting = false;
					}
					
					$scope.$apply();
				};
				
				source.onerror = function(event) {
					self.submitting = false;
					self.response.update.status = "error";
					self.response.update.message = "Error";
					$scope.$apply();
				}
			},
			function(errResp) {
				self.submitting = false;
				ErrorService.open(errResp.data.message);
			});
	};
	
	self.cancel = function() {
		return PathwayGenieService.cancel(jobId);
	};
	
	self.update = function() {
		return self.response.update;
	};
}]);