tagInputApp.controller("tagInputCtrl", [function() {
	var self = this;
	self.tagText = null;
	
	self.addTag = function(tags) {
		if(!tags.includes(self.tagText.toUpperCase())) {
			tags.push(self.tagText.toUpperCase());
		}
		self.tagText = null
	};
}]);