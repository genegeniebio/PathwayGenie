designApp.directive("featurePanel", function() {
    return {
    	scope: {
    		selected: "&",
    		setValid: "&"
    	},
        templateUrl: "feature.html",
        link: function (scope, element, attr, ctrl) {
            scope.$watch("form.$valid", function() {
            	scope.setValid({valid: scope.form.$valid});
            });
        }
    };
});