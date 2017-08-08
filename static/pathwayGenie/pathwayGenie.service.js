pathwayGenieApp.factory("PathwayGenieService", ["$http", "ErrorService", function($http, ErrorService) {
	var restrEnzs = [];
	
	var restrEnzymesPromise = $http.get("/restr_enzymes").then(
		function(resp) {
			restrEnzs.push.apply(restrEnzs, resp.data);
		},
		function(errResp) {
			ErrorService.open(errResp.data.message);
		});
	return {
		restrEnzymesPromise: restrEnzymesPromise,
		restrEnzs: restrEnzs,

		submit: function(query) {
			return $http.post("/submit", query);
		},
		
		cancel: function(jobId) {
			return $http.get("/cancel/" + jobId);
		}
	}
}]);