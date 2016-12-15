progressApp.controller('progressInstanceCtrl', ["$scope", "$uibModalInstance", "ErrorService", "progressTitle", "cancel", "update", function($scope, $uibModalInstance, ErrorService, progressTitle, cancel, update) {
	var self = this;
	var googleLoaded = false;
	self.progressTitle = progressTitle;
	self.cancel = cancel;
	self.update = update;

	self.init = function() {
		google.charts.load('visualization', '1.0', {
			packages: ['gauge'],
			callback: function() {
				googleLoaded = true;
			}
		});
	};

	self.range = function(min, max, step) {
		step = step || 1;
		var input = [];
		for(i = min; i < max; i += step) {
			input.push(i);
		}
		return input;
	};

	self.doCancel = function() {
		self.close();

		self.cancel().then(
				function(resp) {
					// No action required
				},
				function(errResp) {
					ErrorService.open(errResp.data.message);
				});
	};

	self.close = function() {
		$uibModalInstance.close();
	};

	$scope.$watch(function() {
		return update().values;
	},               
	function(values) {
		if(values) {
			for(i=0; i < values.length; i++) {
				drawChart(i, values[i]);
			}
		}
	}, true);

	drawChart = function(index, values) {
		if(googleLoaded) {
			var data = google.visualization.arrayToDataTable([["Label", "Value"],
			                                                  [values['name'],
			                                                   parseFloat(values['value'].toPrecision(4))]]);                                     	
			var options = {
					height: 120,
					min: values['min'],
					max: values['max'],
					greenFrom: values['target'] - values['max'] / 20,
					greenTo: values['target'] + values['max'] / 20
			};

			var element = document.getElementById("progress-gauge-" + index);
			
			if(element) {
				var chart = new google.visualization.Gauge(element);
				chart.draw(data, options);
			}
		}
	}
}]);