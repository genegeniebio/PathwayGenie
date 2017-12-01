dnaApp.directive("dnaPanel", function() {
	return {
		scope: {
			"dna": "=",
			"selected": "&",
			"toggleSelected": "&",
			"format": "&"
		},
		templateUrl: "/static/dna/dna.html",
		link: function($scope, element, attrs) {
            $scope.format = function(value) {
	        		if(Number(value) === value && value % 1 !== 0) {
	        			// if is float:
	        			return value.toPrecision(3);
	        		}
	        		// else:
	        		return value;
	        	}
        }
	};
});