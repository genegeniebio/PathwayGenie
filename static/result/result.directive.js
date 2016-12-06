resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"saveResults": "&",
    		"connected": "&"
    	},
        templateUrl: "/static/result/result.html"
    };
});