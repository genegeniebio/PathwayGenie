metResultApp.factory("MetResultService", [function() {
	var obj = {};
	obj.results = null;
	obj.result = null;
	
	var currentResult = 0;
	
	obj.setResults = function(res) {
		obj.results = res;
		obj.setCurrentResult(0);
	}
	
	obj.setCurrentResult = function(currentRes) {
		currentResult = currentRes;
		
		if(obj.results) {
			obj.result = obj.results[currentResult];
		}
		else {
			obj.result = null;
		}
	}
	
	return obj;
}]);