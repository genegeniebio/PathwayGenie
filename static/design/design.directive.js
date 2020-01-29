designApp.directive("designPanel", function($timeout) {
    return {
    	scope: {
    		templates: "=",
    		query: "&",
    		selected: "&",
    		toggleSelected: "&",
    		addDesign: "&",
    		copyDesign: "&",
    		removeDesign: "&",
    		addFeature: "&",
    		copyFeature: "&",
    		bulkUniprot: "&",
    		pagination: "="
    	},
        templateUrl: "/static/design/design.html",
        link: function(scope, element) {
        	scope.$watch(function() {
        		return scope.query().designs;
        	},               
        	function(designs) {
        		$timeout(checkValidity(scope, designs));
        	}, true);
        	
        	checkValidity = function(scope, designs) {
        		var valid = true;
        		
        		for(var i = 0; i < designs.length; i++) {
        			design = designs[i];
        			
        			for(var j = 0; j < design.features.length; j++) {
        				feature = design.features[j];
        				
        				// If RBS not followed by CDS:
        				if(feature.typ == "http://identifiers.org/so/SO:0000139") {
        					feature.temp_params.valid = j != design.features.length - 1
        						&& design.features[j + 1].typ == "http://identifiers.org/so/SO:0000316";
        				}
        				
        				if(!feature.temp_params.valid) {
        					var id = feature.temp_params.id;
        					valid = false;
        				}
        			}
        		}
        		
        		scope.$parent.form.$setValidity("valid", valid);
        	}
        }
    };
});