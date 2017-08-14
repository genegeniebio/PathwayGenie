resultApp.factory("ResultService", ["$http", "$rootScope", "ICEService", "ErrorService", function($http, $rootScope, ICEService, ErrorService) {
	var obj = {};
	obj.results = null;

	obj.setResults = function(res) {
		obj.results = res;
	}
	
	obj.appendResults = function(res) {
		if(!obj.results) {
			obj.results = [];
		}
		
		obj.results.push.apply(obj.results, res);
	}

	obj.saveResults = function() {
		$http.post("/save", {"result": obj.results, "ice": ICEService.ice}).then(
				function(resp) {
					for (i = 0; i < resp.data.length; i++) {
						if(obj.results[i].links.indexOf(resp.data[i]) == -1 ) {
							obj.results[i].links.push(resp.data[i]);
						}
					}
				},
				function(errResp) {
					ErrorService.open(errResp.data.message);
				});
	}

	return obj;
}]);