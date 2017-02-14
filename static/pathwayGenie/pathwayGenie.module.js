var pathwayGenieApp = angular.module("pathwayGenieApp", ["ngRoute", "assemblyGenieApp", "dominoGenieApp", "iceApp", "metabolomicsGenieApp", "partsGenieApp", "sbcdoeApp"]);

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
	).when("/partsGenie", {
		controller: "partsGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/partsGenie.html",
		app: "PartsGenie",
		resolve: {
			"unused": function(PathwayGenieService) {
				return PathwayGenieService.restr_enzymes_promise;
			}
		}}
	)
	.when("/sbcdoe", {
		controller: "sbcdoeCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/sbcdoe.html",
		app: "SBC-DoE"
		}
	).when("/dominoGenie", {
		controller: "dominoGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/dominoGenie.html",
		app: "DominoGenie",
		resolve: {
			"unused": function(PathwayGenieService) {
				return PathwayGenieService.restr_enzymes_promise;
			}
		}}
	).when("/assemblyGenie", {
		controller: "assemblyGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/assemblyGenie.html",
		app: "AssemblyGenie"
		}
	).when("/metabolomicsGenie", {
		controller: "metabolomicsGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/metabolomicsGenie.html",
		app: "MetabolomicsGenie"
		}
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