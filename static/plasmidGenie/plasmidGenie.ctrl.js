plasmidGenieApp.controller("plasmidGenieCtrl", ["$scope", "ErrorService", "ICEService", "PathwayGenieService", "ProgressService", "ResultService", function($scope, ErrorService, ICEService, PathwayGenieService, ProgressService, ResultService) {
	var self = this;
	self.file_name = null;
	self.file_content = null
	
	self.query = {
			"app": "PlasmidGenie",
			"melt_temp": 70,
			"circular": true,
			"restr_enzs": []
		};
	
	self.response = {"update": {}};
	
	self.restrEnzs = PathwayGenieService.restrEnzs;
	
	var jobIds = [];
	var jobId = null;
	
	self.selectRestEnzs = function(selected) {
		self.restrEnzs = remove(self.restrEnzs, selected);
		self.query.restr_enzs.push.apply(self.query.restr_enzs, selected);
	}
	
	self.deselectRestEnzs = function(selected) {
		self.restrEnzs.push.apply(self.restrEnzs, selected);
		self.query.restr_enzs = remove(self.query.restr_enzs, selected);
	}

	self.connected = function() {
		return ICEService.connected;
	}
	
	self.submit = function() {
		reset();
		
		ProgressService.open(self.query["app"] + " dashboard", self.cancel, self.update);
		
		// Merge self.query and ICE parameters.
		var query = $.extend({}, self.query, {'ice': ICEService.ice});
		
		PathwayGenieService.submit(query).then(
			function(resp) {
				jobIds = resp.data.job_ids;
				listen();
			},
			function(errResp) {
				ErrorService.open(errResp.data.message);
			});
	};
	
	self.cancel = function() {
		return PathwayGenieService.cancel(jobId);
	};
	
	self.update = function() {
		return self.response.update;
	};
	
	listen = function() {
		if(jobIds.length == 0) {
			return;
		}
		
		jobId = jobIds[0];
		var source = new EventSource("/progress/" + jobId);

		source.onmessage = function(event) {
			self.response = JSON.parse(event.data);
			status = self.response.update.status;
			
			if(status == "cancelled" || status == "error" || status == "finished") {
				source.close();

				if(status == "finished") {
					ResultService.appendResults(self.response.result);
				}
				
				jobIds.splice(0, 1);
				listen();
			}
			
			$scope.$apply();
		};
		
		source.onerror = function(event) {
			source.close();
			jobIds.splice(0, 1);
			listen();
			onerror(event.message);
		}
	};
	
	$scope.$watch(function() {
		return self.file_content;
	},               
	function(values) {
		// Parse DoE file:
		if(values) {
			var lines = values.match(/[^\r\n]+/g);
			
			var designs = []
			
			for(var i=0; i < lines.length; i++) {
				tokens = lines[i].split(/(\s+)/).filter(
					function(e) {
						return e.trim().length > 0;
						}
					);
				designs.push({"name": tokens[0], "design": tokens.slice(1, tokens.length)})
			}
			
			self.query.designs = designs;
		}
	}, true);

	reset = function() {
		status = {"update": {}};
		jobIds = [];
		jobId = null;
		error = null;
		ResultService.setResults(null);
	};
	
	remove = function(array, toRemove) {
		array = array.filter(function(elem) {
			return !toRemove.includes(elem);
		});
		
		return array;
	};
	
	// Initialise UI:
	reset();
}]);