metResultApp.directive("metResultPanel", function() {
    return {
    	scope: {
    		"init": "&",
    		"results": "&",
    		"result": "&",
    		"currentResult": "="
    	},
        templateUrl: "/static/metabolomicsGenie/metResult.html"
    };
});