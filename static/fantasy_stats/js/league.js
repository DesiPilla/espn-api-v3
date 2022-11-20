$(document).ready(function() {
    
   $('#select-from-current-year').show();
   $('#select-from-previous-year').hide();
   
   $("input[name=current-or-previous-season]").on( "change", function() {
      let checkedElement = $('input[name=current-or-previous-season]:checked').val()
      let uncheckedElement = $('input[name=current-or-previous-season]:not(:checked)').val()

      $('#'+checkedElement).show();
      $('#'+uncheckedElement).hide();

      // $('#'+checkedElement).toggle();
      // $('#'+uncheckedElement).toggle();
    } );

});