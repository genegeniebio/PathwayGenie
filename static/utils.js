function getJSON(form)
{
	var json = {};
	var a = form.serializeArray();
	
	$.each(a, function()
	{
		if(json[this.name])
		{
			if(!json[this.name].push)
			{
				json[this.name] = [json[this.name]];
			}
			
			json[this.name].push(this.value || '');
		}
		else
		{
			json[this.name] = this.value || '';
		}
	} );
	
	return JSON.stringify(json);
}


function guid()
{
	function s4()
	{
		return Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
	}
	
	return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
}