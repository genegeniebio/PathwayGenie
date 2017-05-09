typeaheadApp.controller("typeaheadCtrl", ["TypeaheadService", function(TypeaheadService) {
	var self = this;
	self.url = null;

	self.getItem = function(terms) {
		return TypeaheadService.getItem(self.url, terms);
	};
}]);