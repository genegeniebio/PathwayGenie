partsGenieApp.controller("partsGenieCtrl", ["$scope", "ErrorService", "PathwayGenieService", "ProgressService", "ResultService", function($scope, ErrorService, PathwayGenieService, ProgressService, ResultService) {
	var self = this;
	self.query = {
			"app": "PartsGenie",
			"designs": [
				{
					"dna": {
						"name": "",
						"desc": "",
						"features": [
							{"typ": "http://purl.obolibrary.org/obo/SO_0001416", "seq": "", "name": "5\' flanking region", "temp_params": {"fixed": true}},
							{"typ": "http://purl.obolibrary.org/obo/SO_0000139", "end": 60, "name": "ribosome entry site", "parameters": {"TIR target": 15000}, "temp_params": {"fixed": false}},
							{"typ": "http://purl.obolibrary.org/obo/SO_0000316", "options": [{"typ": "http://purl.obolibrary.org/obo/SO_0000316", "name": "coding sequence", "temp_params": {"aa_seq": "", "fixed": false}}]},
							{"typ": "http://purl.obolibrary.org/obo/SO_0001417", "seq": "", "name": "3\' flanking region", "temp_params": {"fixed": true}}
						]
					}
				}
			], 
			"filters": {
				"max_repeats": 6
			},
		};
	self.response = {"update": {"values": []}};
	self.excl_codons_regex = "([ACGTacgt]{3}(\s[ACGTacgt]{3})+)*";
	
	var jobId = null;
	
	self.restr_enzs = function() {
		return PathwayGenieService.restr_enzs();
	};
	
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