    $("#filmography-toggle").click(function () {
        $("#filmography-list").toggle();
    });
$("#links-toggle").click(function () {
        $("#link-list").toggle();
    });
        $(".btn-expand").click(function () {
            id = $(this).attr("id");
            number = id.split("-")[id.split("-").length - 1];

            $("#movie-content-" + number).toggle();
            if ($(this).text() == "Zwiń") {
                $(this).text("Rozwiń")
            } else {
                $(this).text("Zwiń")
            }
        });
