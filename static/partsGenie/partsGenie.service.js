partsGenieApp.factory("PartsGenieService", ["$http", function($http) {
	var obj = {};
	
	obj.query = {
		"app": "PartsGenie",
		"designs": [
			
		], 
		"filters": {
			"max_repeats": 5
		},
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

	return obj;
}]);