resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"saveResults": "&",
    		"connected": "&",
    		"selected": "&",
    		"toggleSelected": "&",
    		"pagination": "=",
    	},
        templateUrl: "/static/result/result.html"
    };
});