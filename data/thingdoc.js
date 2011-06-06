$(document).ready(function(){

	$("#bombutton").click(function(){
		$("#bom").animate({ height: 'show', opacity: 'show' }, 'fast');
		$("#things").animate({ height: 'hide', opacity: 'hide' }, 'fast');
		$("#assembly").animate({ height: 'hide', opacity: 'hide' }, 'fast');
		$("#intro").animate({ height: 'hide', opacity: 'hide' }, 'fast');
	});

	$("#thingsbutton").click(function(){
		$("#bom").animate({ height: 'hide', opacity: 'hide' }, 'fast');
		$("#things").animate({ height: 'show', opacity: 'show' }, 'fast');
		$("#assembly").animate({ height: 'hide', opacity: 'hide' }, 'fast');
		$("#intro").animate({ height: 'hide', opacity: 'hide' }, 'fast');
	});

	$("#assemblybutton").click(function(){
		$("#bom").animate({ height: 'hide', opacity: 'hide' }, 'fast');
		$("#things").animate({ height: 'hide', opacity: 'hide' }, 'fast');
		$("#assembly").animate({ height: 'show', opacity: 'show' }, 'fast');
		$("#intro").animate({ height: 'hide', opacity: 'hide' }, 'fast');
	});

});
