metResultApp.controller("metResultCtrl", ["$scope", "MetResultService", function($scope, MetResultService) {
	var self = this;
	var googleLoaded = false;

	self.currentResult = 0;

	self.init = function() {
		google.charts.load('current', {
			packages: ['corechart', 'bar'],
			callback: function() {
				googleLoaded = true;
			}
		});
	};

	self.results = function() {
		return MetResultService.results;
	};

	self.result = function() {
		if(self.results()) {
			return self.results()[self.currentResult];
		}
		else {
			return null;
		}
	};
	
	$scope.$watch(function() {
		return self.result();
	},               
	function(result) {
		if(result) {
			drawSpectrum(result.hits[0].spectrum.peaks);
		}
	}, true);

	drawSpectrum = function(peaks) {
		if(googleLoaded) {
			var data = new google.visualization.DataTable();
			data.addColumn('number', 'm/z');
			data.addColumn('number', 'Result');

			data.addRows(peaks);

			var options = {
					title: 'Spectrum',
					hAxis: {
						title: 'm/z',
					},
					vAxis: {
						title: 'Intensity'
					}
			};
			
			var chart = new google.visualization.ColumnChart(
					document.getElementById('chart_div'));

			chart.draw(data, options);
		}
	}
}]);