dnaApp.directive("dnaPanel", function() {
    return {
    	scope: {
    		"dna": "="
    	},
        templateUrl: "/static/dna/dna.html"
    };
});