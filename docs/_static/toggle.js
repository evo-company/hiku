$(document).ready(function() {
    $(".toggle > *").hide();
    $(".toggle .header").show().click(function() {
        $(this).parent().children().not(".header").toggle(100);
        $(this).parent().children(".header").toggleClass("open");
    })
});
