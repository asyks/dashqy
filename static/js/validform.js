$(function() {

	$('#multi').change(function() {
		$selected = $('#multi option:selected');
		numSelect = $selected.length;
		maxOptions = 10;
		first = $selected.index() 	
		if ($selected.length > maxOptions) {
			$selected.each(function() {
				$(this).removeAttr('selected');
			});
		}
	});

	$('#start-date').change(function() {
		startDate = Date.parse($(this).val());
		endDate = Date.parse($('#end-date').val());
		if (startDate > endDate) {
			$(this).val('');
			$('#end-date').val('');
		}
	});

	$('#end-date').change(function() {
		startDate = Date.parse($('#start-date').val());
		endDate = Date.parse($(this).val());
		if (endDate < startDate) {
			$('#start-date').val('');
			$(this).val('');
		}
	});

});
