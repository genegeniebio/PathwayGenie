var pathwayGenieApp = angular.module("pathwayGenieApp", ["ngRoute", "iceApp", "partsGenieApp"]);

pathwayGenieApp.config(function($routeProvider, $locationProvider) {
	$routeProvider.when("/", {
		controller: "partsGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/partsGenie.html",
		app: "PartsGenie",
		resolve: {
			"unused": function(PathwayGenieService) {
				return PathwayGenieService.restr_enzymes_promise;
			}
		}}
	).when("/ice", {
		controller: "iceCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/ice.html",
		app: "ICE"
		}
	)
	
	// Use the HTML5 History API:
    $locationProvider.html5Mode(true);
});