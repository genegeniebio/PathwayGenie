designApp.controller("designCtrl", ["$scope", "DesignService", "UniprotService", function($scope, DesignService, UniprotService) {
	var self = this;
	
	var search = false;
	
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
			type: "feature",
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
			type: "feature",
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
			type: "feature",
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
			type: "feature",
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
	
	self.query = function() {
		return DesignService.query;
	};
	
	self.selected = function() {
		return DesignService.selected;
	};
	
	self.toggleSelected = function(selected) {
		return DesignService.toggleSelected(selected);
	};
	
	self.setValid = function(valid) {
		if(DesignService.selected) {
			DesignService.selected.temp_params.valid = valid;
		}
	};
	
	self.addDesign = function() {
		self.query().designs.push({
			type: "design",
			name: "Design",
			desc: "Design",
			features: []
		});
	};
	
	self.removeDesign = function(index) {
		self.query().designs.splice(index, 1);
		self.toggleSelected(null);
	};
	
	self.searchUniprot = function(query) {
		search = true;
		
		DesignService.searchUniprot(query).then(
			function(resp) {
				UniprotService.open(resp.data, DesignService.selected)
				search = false;
			},
			function(errResp) {
				search = false;
			});
	};
	
	self.searching = function() {
		return search;
	}

	self.queryJson = angular.toJson({selected: self.selected(), query: self.query()}, true);
	
	$scope.$watch(function() {
		return self.selected();
	},               
	function(values) {
		self.queryJson = angular.toJson({selected: self.selected(), query: self.query()}, true)
	}, true);
	
	$scope.$watch(function() {
		return self.query();
	},               
	function(values) {
		self.queryJson = angular.toJson({selected: self.selected(), query: self.query()}, true)
	}, true);

	// Initialise UI:
	self.addDesign();
}]);