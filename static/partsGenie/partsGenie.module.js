var partsGenieApp = angular.module("partsGenieApp", ["ngRoute", "errorApp", "progressApp", "resultApp", "typeaheadApp"]);

partsGenieApp.config(function($routeProvider) {
	$routeProvider.when("/", {
		controller: "partsGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/partsgenie.html",
		resolve: {
			"unused": function(PartsGenieService) {
				return PartsGenieService.restr_enzymes_promise;
			}
		}})
});