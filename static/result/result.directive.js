resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"saveResults": "&",
    		"connected": "&",
    		"feature": "&",
    	},
        templateUrl: "/static/result/result.html"
    };
});