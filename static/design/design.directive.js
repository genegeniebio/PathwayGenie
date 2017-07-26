designApp.directive("designPanel", function($timeout) {
    return {
    	scope: {
    		templates: "=",
    		query: "&",
    		selected: "&",
    		toggleSelected: "&",
    		addDesign: "&",
    		removeDesign: "&",
    		copy: "&"
    	},
        templateUrl: "design.html",
        link: function(scope, element) {
        	scope.$watch(function() {
        		return scope.query().designs;
        	},               
        	function(designs) {
        		$timeout(checkValidity(designs));
        	}, true);
        	
        	checkValidity = function(designs) {
        		for(var i = 0; i < designs.length; i++) {
        			design = designs[i];
        			
        			for(var j = 0; j < design.features.length; j++) {
        				feature = design.features[j];
        				
        				if(!feature.temp_params.valid) {
        					var id = feature.temp_params.id;
        					var form = element.find("form").eq(0);
        					ctrl = form.controller("form");
        					ctrl.$setValidity("valid", false);
        				}
        			}
        		}
        	}
        }
    };
});