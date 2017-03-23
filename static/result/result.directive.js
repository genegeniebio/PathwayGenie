resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"saveResults": "&",
    		"connected": "&",
    		"feature": "&",
    		"setFeature": "&",
    		"pagination": "=",
    	},
        templateUrl: "/static/result/result.html"
    };
});