tagInputApp.directive("tagInput", function() {
	return {
		scope: {
			placeholder: "=",
			tags: "=",
			pattern: "=",
			tagText: "=",
			addTag: "&",
			validTag: "&"
		},
		templateUrl : "/static/tagInput/tagInput.html"
	};
});