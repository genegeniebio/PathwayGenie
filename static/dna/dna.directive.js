dnaApp.directive("dnaPanel", function() {
	return {
		scope: {
			"dna": "=",
			"selected": "&",
			"setSelected": "&"
		},
		templateUrl: "/static/dna/dna.html",
	};
});