designApp.directive("designPanel", function() {
    return {
    	scope: {
    		templates: "=",
    		query: "&",
    		selected: "&",
    		toggleSelected: "&",
    		addDesign: "&",
    		removeDesign: "&",
    	},
        templateUrl: "design.html"
    };
});