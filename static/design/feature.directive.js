designApp.directive("featurePanel", function() {
    return {
    	scope: {
    		selected: "&",
    		setValid: "&",
    		searchUniprot: "&",
    		searching: "&"
    	},
        templateUrl: "/static/design/feature.html",
        link: function (scope, element, attr, ctrl) {
            scope.$watch("form.$valid", function(newVal) {
            	scope.setValid({valid: newVal});
            });
        }
    };
});