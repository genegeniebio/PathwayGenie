resultApp.factory("ResultService", ["$http", "ICEService", "ErrorService", function($http, ICEService, ErrorService) {
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
	
	obj.saveResults = function() {
		$http.post("/save", {'result': obj.results, 'ice': ICEService.ice}).then(
				function(resp) {
					for (i = 0; i < resp.data.length; i++) {
						obj.results[i].links.push(resp.data[i]);
					}
				},
				function(errResp) {
					ErrorService.open(errResp.data.message);
				});
	}
	
	return obj;
}]);