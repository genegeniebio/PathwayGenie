uniprotApp.controller("uniprotCtrl", ["$uibModalInstance", "options", function($uibModalInstance, options) {
	var self = this;
	self.options = options;
	
	self.cancel = function() {
		$uibModalInstance.close();
	};

	self.ok = function() {
		$uibModalInstance.close();
	};
}]);