$(function() {
  $(".js-propose-swap").click(function() {
    var $button = $(this);
    var userId = $button.data().profileId;
    var name = $button.data().name;
    $.confirm({
      title: 'Propose swap?',
      content: "Are you sure you want to propose a swap with " + name + "?",
      confirmButton: "Yes!",
      cancelButton: "Cancel",
      confirm: function(){
        $button.prop("disabled", true);

        $.post("/user/swap/",
               { to_profile: userId, csrfmiddlewaretoken: vs.csrf })
          .done(function() {
            $button.parents(".js-swap-option").addClass("proposed");
          })
          .fail(function() {
            $button.prop("disabled", false);
            $.alert("Unfortunately we were not able to confirm that swap. " +
                    "Please try again");
          });
      },
      cancel: function(){
      }
    });
  });
});
