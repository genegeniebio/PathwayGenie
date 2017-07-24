designApp.controller("designCtrl", ["$scope", "DesignService", function($scope, DesignService) {
	var self = this;
	
	self.templates = [
		{
			typ: "http://purl.obolibrary.org/obo/SO_0001416",
			name: "5' flanking region",
			seq: "",
			valid: false,
			temp_params: {
				fixed: true,
				seq_required: true
			}
		},
		{
			typ: "http://purl.obolibrary.org/obo/SO_0000143",
			name: "assembly component",
			seq: "",
			valid: true,
			parameters: {
				"Tm target": 70
			},
			temp_params: {
				fixed: true
			}
		},
		{
			type: "feature",
			typ: "http://purl.obolibrary.org/obo/SO_0000167",
			name: "promoter",
			seq: "",
			valid: false,
			temp_params: {
				fixed: true,
				seq_required: true
			}
		},
		{
			type: "feature",
			typ: "http://purl.obolibrary.org/obo/SO_0000139",
			name:"ribosome entry site",
			end: 60,
			valid: true,
			parameters: {
				"TIR target": 15000
			},
			temp_params: {
				fixed: false,
				min_end: 35,
				max_end: 10000,
			}
		},
		{
			type: "feature",
			typ: "http://purl.obolibrary.org/obo/SO_0000316",
			name: "coding sequence",
			valid: false,
			options: [
				{
					typ: "http://purl.obolibrary.org/obo/SO_0000316",
					name: "coding sequence",
					temp_params: {
						fixed: false
					}
				}
			]
		},
		{
			type: "feature",
			typ: "http://purl.obolibrary.org/obo/SO_0000141",
			name: "terminator",
			seq: "",
			valid: false,
			temp_params: {
				fixed: true,
				seq_required: true
			}
		},
		{
			typ: "http://purl.obolibrary.org/obo/SO_0000449",
			end: 100,
			name: "random region",
			valid: true,
			temp_params: {
				fixed: false,
				min_end: 1,
				max_end: 10000
			}
		},
		{
			typ: "http://purl.obolibrary.org/obo/SO_0001417",
			name: "3' flanking region",
			seq: "",
			valid: false,
			temp_params: {
				fixed: true,
				seq_required: true
			}
		}
	];
	
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
			DesignService.selected.valid = valid;
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