dnaApp.directive("dnaPanel", function() {
    return {
    	scope: {
    		"dna": "=",
    		"feat": "&",
    		"setFeat": "&"
    	},
        templateUrl: "/static/dna/dna.html"
    };
});