progressApp.factory("ProgressService", ["$uibModal", function($uibModal) {
	var obj = {};
	
	obj.open = function(progressTitle, cancel, update) {
		$uibModal.open({
			animation: true,
			ariaLabelledBy: 'modal-title',
			ariaDescribedBy: 'modal-body',
			templateUrl: '/static/progress/progressContent.html',
			controller: 'progressInstanceCtrl',
			controllerAs: 'progressCtrl',
			backdrop: 'static',
			keyboard: false,
			resolve: {
				progressTitle: function() {
					return progressTitle;
				},
				cancel: function() {
					return cancel;
				},
				update: function() {
					return update;
				}
			}
		});
	};
	
	return obj;
}]);