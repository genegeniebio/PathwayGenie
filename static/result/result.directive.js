resultApp.directive("resultPanel", function() {
    return {
    	scope: {
    		"results": "&",
    		"result": "&",
    		"sbol": "&",
    		"saveResults": "&",
    		"ice": "="
    	},
        templateUrl: "/static/result/result.html"
    };
});