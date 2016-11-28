resultApp.factory("ResultService", ["$http", "ErrorService", function($http, ErrorService) {
	var obj = {};
	obj.results = null;
	obj.result = null;
	obj.sbol = null;
	
	var currentResult = 0;
	
	obj.setResults = function(res) {
		obj.results = res;
		obj.setCurrentResult(0);
	}
	
	obj.setCurrentResult = function(currentRes) {
		currentResult = currentRes;
		
		if(obj.results) {
			obj.result = obj.results[currentResult];
			
			$http.get("/result/" + obj.result.data.file).then(
				function(resp) {
					obj.sbol = resp.data;
				},
				function(errResp) {
					ErrorService.open(errResp.data.message);
				});
		}
		else {
			obj.result = null;
		}
	}
	
	obj.saveResults = function(ice) {
		$http.post("/save", {'result': obj.results, 'ice': ice}).then(
				function(resp) {
					for (i = 0; i < resp.data.length; i++) {
						obj.results[i].metadata.links.push(resp.data[i]);
					}
				},
				function(errResp) {
					ErrorService.open(errResp.data.message);
				});
	}
	
	return obj;
}]);