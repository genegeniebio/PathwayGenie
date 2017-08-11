dnaApp.directive("dnaPanel", function() {
	return {
		scope: {
			"dna": "=",
			"selected": "&",
			"toggleSelected": "&"
		},
		templateUrl: "/static/dna/dna.html",
	};
});