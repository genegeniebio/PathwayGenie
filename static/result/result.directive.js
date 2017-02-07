resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"saveResults": "&",
    		"connected": "&",
    		"feature": "&",
    		"setFeature": "&",
    	},
        templateUrl: "/static/result/result.html"
    };
});