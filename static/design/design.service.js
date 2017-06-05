designApp.factory("DesignService", [function() {
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

	return obj;
}]);