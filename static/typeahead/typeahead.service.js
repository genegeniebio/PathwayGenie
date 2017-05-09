typeaheadApp.factory("TypeaheadService", ["$http", "ErrorService", function($http, ErrorService) {
	var obj = {};
	
	obj.getItem = function(url, terms) {
		return $http.post(url, terms).then(
				function(resp) {
					return resp.data.map(function(item) {
						return item;
					});
				},
				function(errResp) {
					ErrorService.open(errResp.data.message);
				});
	};

	return obj;
}]);