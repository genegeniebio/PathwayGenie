iceApp.controller("iceInstanceCtrl", ["$uibModalInstance", "ICEService", "TypeaheadService", function($uibModalInstance, ICEService, TypeaheadService) {
	var self = this;
	
	self.ice = function() {
		return ICEService.ice;
	};
	
	self.status = function() {
		return ICEService.status;
	}
	
	self.message = function() {
		return ICEService.message;
	}
	
	self.error = function() {
		return ICEService.error;
	}
	
	self.connect = function() {
		return ICEService.connect();
	}
	
	self.disconnect = function() {
		return ICEService.disconnect();
	}
	
	self.searchGroups = function(term) {
		return TypeaheadService.getItem("/groups/", {"term": term, "ice": ICEService.ice});
	}
	
	self.close = function() {
		$uibModalInstance.close();
	};
}]);