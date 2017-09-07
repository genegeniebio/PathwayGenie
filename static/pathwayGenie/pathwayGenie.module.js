var pathwayGenieApp = angular.module("pathwayGenieApp", ["ngRoute", "iceApp", "partsGenieApp", "plasmidGenieApp"]);

pathwayGenieApp.config(function($routeProvider, $locationProvider) {
	$routeProvider.when("/", {
		controller: "partsGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/partsGenie/partsGenie.html",
		app: "PartsGenie",
		resolve: {
			"unused": function(PathwayGenieService) {
				return PathwayGenieService.restr_enzymes_promise;
			}
		}
	}).when("/partsGenie", {
		controller: "partsGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/partsGenie/partsGenie.html",
		app: "PartsGenie",
		resolve: {
			"unused": function(PathwayGenieService) {
				return PathwayGenieService.restr_enzymes_promise;
			}
		}
	}).when("/plasmidGenie", {		
		 controller: "plasmidGenieCtrl",		
		 controllerAs: "ctrl",		
		 templateUrl: "static/plasmidGenie/plasmidGenie.html",		
		 app: "PlasmidGenie"
	})
	
	// Use the HTML5 History API:
    $locationProvider.html5Mode(true);
});