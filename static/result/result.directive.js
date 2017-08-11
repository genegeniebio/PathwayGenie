resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"saveResults": "&",
    		"connected": "&",
    		"selected": "&",
    		"setSelected": "&",
    		"pagination": "=",
    	},
        templateUrl: "/static/result/result.html"
    };
});