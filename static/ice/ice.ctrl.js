iceApp.controller("iceInstanceCtrl", ["$uibModalInstance", "ICEService", "TypeaheadService", function($uibModalInstance, ICEService, TypeaheadService) {
	var self = this;
	
	self.ice = function() {
		return ICEService.ice;
	};
	
	self.connected = function() {
		return ICEService.connected;
	}
	
	self.connecting = function() {
		return ICEService.connecting;
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