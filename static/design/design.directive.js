designApp.directive("designPanel", function() {
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
        link: function(scope, element, attrs, formCtrl) {
        	scope.$watch(function() {
        		return scope.query().designs;
        	},               
        	function(designs) {
        		for(var i = 0; i < designs.length; i++) {
        			design = designs[i];
        			
        			for(var j = 0; j < design.features.length; j++) {
        				feature = design.features[j];
        				
        				if(!feature.temp_params.valid) {
        					var id = '#' + feature.temp_params.id;
        					// var ft = angular.element(element);
        					// ft.$setValidity("valid", false);
        				}
        			}
        		}
        	}, true);
        }
    };
});