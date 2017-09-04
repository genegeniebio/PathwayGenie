var pathwayGenieApp = angular.module("pathwayGenieApp", ["ngRoute", "dominoGenieApp", "iceApp", "designGenieApp"]);

pathwayGenieApp.config(function($routeProvider, $locationProvider) {
	$routeProvider.when("/", {
		controller: "designGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/designGenie/designGenie.html",
		app: "DesignGenie",
		resolve: {
			"unused": function(PathwayGenieService) {
				return PathwayGenieService.restr_enzymes_promise;
			}
		}
	}).when("/designGenie", {
		controller: "designGenieCtrl",
		controllerAs: "ctrl",
		templateUrl: "static/designGenie/designGenie.html",
		app: "DesignGenie",
		resolve: {
			"unused": function(PathwayGenieService) {
				return PathwayGenieService.restr_enzymes_promise;
			}
		}
	}).when("/dominoGenie", {		
		 controller: "dominoGenieCtrl",		
		 controllerAs: "ctrl",		
		 templateUrl: "static/dominoGenie/dominoGenie.html",		
		 app: "DominoGenie"
	})
	
	// Use the HTML5 History API:
    $locationProvider.html5Mode(true);
});