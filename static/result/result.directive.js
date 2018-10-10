resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"exportOrder": "&",
    		"saveResults": "&",
    		"connected": "&",
    		"selected": "&",
    		"toggleSelected": "&",
    		"pagination": "=",
    	},
        templateUrl: "/static/result/result.html"
    };
});