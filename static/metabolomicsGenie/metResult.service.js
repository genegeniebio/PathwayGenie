metResultApp.factory("MetResultService", [function() {
	var obj = {};
	obj.results = null;
	
	obj.setResults = function(res) {
		obj.results = res;
	}
	
	return obj;
}]);