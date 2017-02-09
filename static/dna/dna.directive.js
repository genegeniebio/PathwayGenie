dnaApp.directive("dnaPanel", function() {
	return {
		scope: {
			"dna": "=",
			"feature": "&",
			"setFeature": "&"
		},
		templateUrl: "/static/dna/dna.html",
	};
});