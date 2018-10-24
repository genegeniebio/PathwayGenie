partsGenieApp.factory("PartsGenieService", ["$http", function($http) {
	var obj = {};
	
	obj.query = {
		"app": "PartsGenie",
		"designs": [
			
		], 
		"filters": {
			"max_repeats": 5,
			"gc_min": 0.25,
			"gc_max": 0.65,
			"local_gc_window": 50,
			"local_gc_min": 0.15,
			"local_gc_max": 0.8,
			"restr_enzs": [],
			"excl_codons": []
		},
	};
	
	obj.addDesign = function() {
		obj.query.designs.push({
			name: "Part",
			desc: "Part",
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