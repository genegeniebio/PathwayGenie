resultApp.factory("ResultService", ["$http", "$rootScope", "ICEService", "ErrorService", function($http, $rootScope, ICEService, ErrorService) {
	var obj = {};
	obj.results = null;

	obj.setResults = function(res) {
		obj.results = res;
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