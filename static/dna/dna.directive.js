dnaApp.directive("dnaPanel", function() {
    return {
    	scope: {
    		"dna": "=",
    		"feature": "=",
    	},
        templateUrl: "/static/dna/dna.html"
    };
});