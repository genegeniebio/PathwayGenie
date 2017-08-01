uniprotApp.controller("uniprotCtrl", ["$uibModalInstance", "options", "feature", function($uibModalInstance, options, feature) {
	var self = this;
	self.options = options;
	self.feature = feature;
	self.selected = null;
	
	self.toggleSelected = function(selected) {
		if(self.selected === selected) {
			self.selected = null;
		}
		else {
			self.selected = selected;
		}
	};
	
	self.cancel = function() {
		$uibModalInstance.dismiss();
	};

	self.ok = function() {
		$uibModalInstance.close(self.selected);
	};
}]);