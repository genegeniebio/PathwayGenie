uniprotTermsApp.controller("uniprotTermsCtrl", ["$uibModalInstance", function($uibModalInstance) {
	var self = this;
	
	self.uniprotTerms = null;
	
	self.ok = function() {
		ids = self.uniprotTerms.split(/,?\s+/);
		$uibModalInstance.close(ids);  
		$uibModalInstance.close();
	};
	
	self.cancel = function() {
		$uibModalInstance.close([]);
	};
}]);