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
			feature.options[0].name = selected["Entry name"];
			feature.options[0].temp_params.aa_seq = selected.Sequence;
			feature.options[0].temp_params.orig_seq = selected.Sequence;
			feature.options[0].desc = selected["Protein names"].join(", ") + " (" + selected["Organism"] + ")";
			
			feature.options[0].links = [
		        "http://identifiers.org/uniprot/" + selected["Entry"]
		    ]
	
		    if(selected["EC number"]) {
		    	feature.options[0].links.push("http://identifiers.org/ec-code/" + selected["EC number"]);
		    }
		});
	};
	
	return obj;
}]);