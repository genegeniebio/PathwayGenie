pathwayGenieApp.factory("PathwayGenieService", ["$http", "ErrorService", function($http, ErrorService) {
	var restr_enzs = null;
	
	var restr_enzymes_promise = $http.get("/restr_enzymes").then(
		function(resp) {
			restr_enzs = resp.data;
		},
		function(errResp) {
			ErrorService.open(errResp.data.message);
		});
	return {
		restr_enzymes_promise: restr_enzymes_promise,
		
		restr_enzs: function() {
			return restr_enzs;
		},

		submit: function(query) {
			return $http.post("/submit", query);
		},
		
		cancel: function(jobId) {
			return $http.get("/cancel/" + jobId);
		}
	}
}]);