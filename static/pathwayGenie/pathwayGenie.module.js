var pathwayGenieApp = angular.module("pathwayGenieApp", ["ngRoute", "helpApp", "iceApp", "partsGenieApp", "plasmidGenieApp"]);

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
	}).when("/lcrGenie", {		
		 controller: "lcrGenieCtrl",		
		 controllerAs: "ctrl",		
		 templateUrl: "static/lcrGenie/lcrGenie.html",		
		 app: "LcrGenie"
	})
	
	
	// Use the HTML5 History API:
    $locationProvider.html5Mode(true);
});