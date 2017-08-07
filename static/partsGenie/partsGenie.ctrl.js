partsGenieApp.controller("partsGenieCtrl", ["$scope", "ErrorService", "PartsGenieService", "PathwayGenieService", "ProgressService", "ResultService", "UniprotService", function($scope, ErrorService, PartsGenieService, PathwayGenieService, ProgressService, ResultService, UniprotService) {
	var self = this;
	var jobId = null;
	var search = false;
	
	self.excl_codons_regex = "([ACGTacgt]{3}(\s[ACGTacgt]{3})+)*";
	self.query = PartsGenieService.query;
	self.response = {"update": {"values": [], "status": "waiting", "message": "Waiting..."}};

	self.restr_enzs = function() {
		return PathwayGenieService.restr_enzs();
	};

	self.templates = [
		{
			typ: "http://purl.obolibrary.org/obo/SO_0001416",
			name: "5' flanking region",
			seq: "",
			temp_params: {
				fixed: true,
				required: ["name", "seq"],
				valid: false,
				id: "_1"
			}
		},
		{
			typ: "http://purl.obolibrary.org/obo/SO_0000143",
			name: "assembly component",
			seq: "",
			parameters: {
				"Tm target": 70
			},
			temp_params: {
				fixed: true,
				required: ["name", "tm"],
				valid: true,
				id: "_2"
			}
		},
		{
			typ: "http://purl.obolibrary.org/obo/SO_0000167",
			name: "promoter",
			seq: "",
			temp_params: {
				fixed: true,
				required: ["name", "seq"],
				valid: false,
				id: "_3"
			}
		},
		{
			typ: "http://purl.obolibrary.org/obo/SO_0000139",
			name:"ribosome entry site",
			end: 60,
			parameters: {
				"TIR target": 15000
			},
			temp_params: {
				fixed: false,
				required: ["name", "tir"],
				min_end: 35,
				max_end: 10000,
				valid: true,
				id: "_4"
			}
		},
		{
			typ: "http://purl.obolibrary.org/obo/SO_0000316",
			name: "coding sequence",
			options: [
				{
					typ: "http://purl.obolibrary.org/obo/SO_0000316",
					name: "coding sequence",
					temp_params: {
						fixed: false
					}
				}
			],
			temp_params: {
				required: ["prot"],
				valid: false,
				id: "_5"
			}
		},
		{
			typ: "http://purl.obolibrary.org/obo/SO_0000141",
			name: "terminator",
			seq: "",
			temp_params: {
				fixed: true,
				required: ["name", "seq"],
				valid: false,
				id: "_6"
			}
		},
		{
			typ: "http://purl.obolibrary.org/obo/SO_0000449",
			end: 100,
			name: "random region",
			temp_params: {
				fixed: false,
				required: ["name", "len"],
				min_end: 1,
				max_end: 10000,
				valid: true,
				id: "_7"
			}
		},
		{
			typ: "http://purl.obolibrary.org/obo/SO_0001417",
			name: "3' flanking region",
			seq: "",
			temp_params: {
				fixed: true,
				required: ["name", "seq"],
				valid: false,
				id: "_8"
			}
		}
	];
	
	self.copy = function(feature) {
		feature.temp_params.id = "_" + (new Date()).getTime();
	}
	
	self.selected = function() {
		return PartsGenieService.selected;
	};
	
	self.toggleSelected = function(selected) {
		return PartsGenieService.toggleSelected(selected);
	};
	
	self.setValid = function(valid) {
		if(PartsGenieService.selected) {
			PartsGenieService.selected.temp_params.valid = valid;
		}
	};
	
	self.addDesign = function() {
		PartsGenieService.addDesign();
	};
	
	self.removeDesign = function(index) {
		self.query.designs.splice(index, 1);
		self.toggleSelected(null);
	};
	
	self.searchUniprot = function(query) {
		search = true;
		
		PartsGenieService.searchUniprot(query).then(
			function(resp) {
				UniprotService.open(resp.data, PartsGenieService.selected)
				search = false;
			},
			function(errResp) {
				search = false;
			});
	};
	
	self.searching = function() {
		return search;
	}

	self.submit = function() {
		jobId = null
		self.response = {"update": {"values": [], "status": "running", "message": "Submitting..."}};
		error = null;
		self.toggleSelected(self.selected);
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
	
	self.queryJson = angular.toJson({selected: self.selected(), query: self.query}, true);
	
	$scope.$watch(function() {
		return self.selected();
	},               
	function(values) {
		self.queryJson = angular.toJson({selected: self.selected(), query: self.query}, true)
	}, true);
	
	$scope.$watch(function() {
		return self.query;
	},               
	function(values) {
		self.queryJson = angular.toJson({selected: self.selected(), query: self.query}, true)
	}, true);
}]);