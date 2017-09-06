partsGenieApp.factory("PartsGenieService", ["$http", function($http) {
	var obj = {};
	
	obj.query = {
		"app": "PartsGenie",
		"designs": [
			
		], 
		"filters": {
			"max_repeats": 5,
			"restr_enzs": [],
			"excl_codons": []
		},
	};
	
	obj.addDesign = function() {
		obj.query.designs.push({
			name: "Design",
			desc: "Design",
			features: []
		});
	};
		
	obj.selected = null;
	
	obj.toggleSelected = function(selected) {
		if(obj.selected === selected) {
			obj.selected = null;
		}
		else {
			obj.selected = selected;
		}
	}
	
	obj.searchUniprot = function(query) {
		return $http.get("/uniprot/" + encodeURIComponent(query));
	}
	
	// Initialise UI:
	obj.addDesign();

	return obj;
}]);