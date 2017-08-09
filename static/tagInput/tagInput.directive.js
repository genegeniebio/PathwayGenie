tagInputApp.directive("tagInput", function() {
	return {
		scope: {
			placeholder: "=",
			tags: "=",
			pattern: "=",
			tagText: "=",
			addTag: "&"
		},
		templateUrl : "/static/tagInput/tagInput.html"
	};
});