dualListboxApp.directive("dualListbox", function() {
    return {
    	scope: {
    		options: "=",
    		chosen: "=",
    		select: "&",
    		deselect: "&"
    	},
        templateUrl: "/static/dualListbox/dualListbox.html"
    };
});