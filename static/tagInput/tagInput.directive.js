tagInputApp.directive("tagInput", function() {
	return {
		scope: {
			placeholder: "=",
			tags: "=",
			tagText: "=",
			addTag: "&"
		},
		templateUrl : "/static/tagInput/tagInput.html"
	};
});