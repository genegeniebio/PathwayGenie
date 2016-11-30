var pathwayGenieApp = angular.module("pathwayGenieApp", ["ngRoute", "assemblyGenieApp", "dominoGenieApp", "partsGenieApp", "sbcdoeApp"]);

pathwayGenieApp.config(function($routeProvider) {
	$routeProvider.when("/", {
		controller: "partsGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/partsGenie.html",
		app: "PartsGenie",
		resolve: {
			"unused": function(PartsGenieService) {
				return PartsGenieService.restr_enzymes_promise;
			}
		}}
	).when("/partsGenie", {
		controller: "partsGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/partsGenie.html",
		app: "PartsGenie",
		resolve: {
			"unused": function(PartsGenieService) {
				return PartsGenieService.restr_enzymes_promise;
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
		app: "DominoGenie"
		}
	).when("/assemblyGenie", {
		controller: "assemblyGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/assemblyGenie.html",
		app: "AssemblyGenie"
		}
)
});