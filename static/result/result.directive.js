resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"sbol": "&",
    		"saveResults": "&",
    	},
        templateUrl: "/static/result/result.html"
    };
});