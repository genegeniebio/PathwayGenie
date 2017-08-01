uniprotApp.controller("uniprotCtrl", ["$uibModalInstance", "options", function($uibModalInstance, options) {
	var self = this;
	self.options = options;
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
		$uibModalInstance.close();
	};

	self.ok = function() {
		$uibModalInstance.close();
	};
}]);