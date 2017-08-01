uniprotApp.factory("UniprotService", ["$uibModal", function($uibModal) {
	var obj = {};
	
	obj.open = function(options) {
		$uibModal.open({
			animation: true,
			ariaLabelledBy: "modal-title",
			ariaDescribedBy: "modal-body",
			templateUrl: "/static/uniprot/uniprot.html",
			controller: "uniprotCtrl",
			controllerAs: "uniprotCtrl",
			backdrop: "static",
			keyboard: false,
			size: "lg",
			resolve: {
				options: function() {
					return options;
				}
			}
		});
	};
	
	return obj;
}]);