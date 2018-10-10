resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"getTwistPlate": "&",
    		"saveResults": "&",
    		"connected": "&",
    		"selected": "&",
    		"toggleSelected": "&",
    		"pagination": "=",
    	},
        templateUrl: "/static/result/result.html"
    };
});