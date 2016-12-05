resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"sbol": "&",
    		"saveResults": "&",
    		"connected": "&"
    	},
        templateUrl: "/static/result/result.html"
    };
});