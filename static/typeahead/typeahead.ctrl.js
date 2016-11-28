typeaheadApp.controller("typeaheadCtrl", ["$http", "ErrorService", function($http, ErrorService) {
	var self = this;
	self.url = null;

	self.getItem = function(val) {
		return $http.get(self.url + val).then(
				function(resp) {
					return resp.data.map(function(item) {
						return item;
					});
				},
				function(errResp) {
					ErrorService.open(errResp.data.message);
				});
	};
}]);