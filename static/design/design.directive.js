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
        templateUrl: "design.html"
    };
});