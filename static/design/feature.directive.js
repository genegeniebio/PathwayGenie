designApp.directive("featurePanel", function() {
    return {
    	scope: {
    		selected: "&",
    	},
        templateUrl: "feature.html"
    };
});