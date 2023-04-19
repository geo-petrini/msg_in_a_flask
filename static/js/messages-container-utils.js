$(document).ready(
    positionMessagesContainer()
)

window.onresize = function () {
    positionMessagesContainer()
}

function positionMessagesContainer() {
    let navbarHeight = $("#navbar").outerHeight();
    let formHeight = $("#form-row").outerHeight();
    let windowWidth = $(window).width();
    let windowHeight = $(window).height();
    // $("#messages-row").width(width);
    let top = navbarHeight
    let height = windowHeight - navbarHeight - formHeight

    // console.log(`vars: navbarHeight: ${navbarHeight}, formHeight ${formHeight} windowHeight ${windowHeight}`)

    $("#messages-row").parent().css({ position: 'relative' });
    $("#messages-row").css({
        top: top,
        height: height,
        position: 'absolute'
    });
    // console.log(`positioning: top: ${top}, height ${height}`)
}