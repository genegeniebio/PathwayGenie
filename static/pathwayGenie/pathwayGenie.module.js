var pathwayGenieApp = angular.module("pathwayGenieApp", ["ngRoute", "assemblyGenieApp", "helpApp", "iceApp", "partsGenieApp", "plasmidGenieApp"]);

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
	}).when("/assemblyGenie", {		
		 controller: "assemblyGenieCtrl",		
		 controllerAs: "ctrl",		
		 templateUrl: "static/assemblyGenie/assemblyGenie.html",		
		 app: "AssemblyGenie"
	})
	
	
	// Use the HTML5 History API:
    $locationProvider.html5Mode(true);
});