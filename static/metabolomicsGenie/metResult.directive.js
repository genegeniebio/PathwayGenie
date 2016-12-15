metResultApp.directive("metResultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    	},
        templateUrl: "/static/metabolomicsGenie/metResult.html"
    };
});