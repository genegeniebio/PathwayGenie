uniprotApp.factory("UniprotService", ["$uibModal", function($uibModal) {
	var obj = {};
	
	obj.open = function(options, feature) {
		var modalInstance = $uibModal.open({
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
				},
				feature: function() {
					return feature;
				}
			}
		});

		modalInstance.result.then(function(selected) {
			feature.options[0].name = selected['Protein names'][0];
			feature.options[0].seq = selected.Sequence;
		});
	};
	
	return obj;
}]);