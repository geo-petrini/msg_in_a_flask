var dz;
var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

socket.on('connect', function () {
    socket.emit('data_event', {
        data: 'user connected'
    })
});


socket.on('response', function (msg) {
    //console.log(msg)
    if (typeof msg.user_name !== 'undefined') {
        displayMessage(msg)
        scrollToLast()
    }
})

function scrollToLast() {
    $("#messages-row").scrollTop($("#message-holder").height());
}

function displayMessage(msg) {
    let message_id = "msg-" + msg.id
    //todo filter messages by id
    if ($("#" + message_id).length == 0) {
        $('#message-holder').append(`
                    <li class="list-group-item" id="${message_id}">
                        <span class="border border-primary rounded p-1">${msg.user_name}</span> ${msg.message}
                    </li>`)
    }
}

var form = $('form').on('submit', function (e) {
    e.preventDefault()
    let user_name = $('input.username').val()
    let user_input = $('input.message').val()
    socket.emit('data_event', {
        user_name: user_name,
        message: user_input
    })
    $('input.message').val('').focus()
})

socket.on('server_status', function (data) {
    // for (var key in msg) { 
    //     console.log(key, msg[key])
    // }   
    updateConnectionStatus(data);
    updateClientsCount(data);
})

function updateConnectionStatus(data) {
    if ((data.db_connection instanceof Boolean && data.db_connection != true) || (data.db_connection instanceof String && data.db_connection.includes("error"))) {
        $('#alert-holder').text(data.db_connection)
        $('#alert-holder').addClass('show')
        $('#alert-holder').removeClass('collapse')
    } else {
        $('#alert-holder').addClass('collapse')
        $('#alert-holder').removeClass('show')
        $('#alert-holder').text("")
    }
}

function updateClientsCount(data) {
    if (data.client_count instanceof Number || (data.client_count instanceof String && !data.client_count.includes("error"))) {
        $('#clients-count').text(data.client_count)
    } else {
        //console.log( msg.client_count )
        $('#clients-count').text(data.client_count)
        $('#clients-count-text').text("Users")
        $('#clients-count-text').parent().addClass("btn")

    }
}

//https://socket.io/how-to/upload-a-file
function upload(files) {
    socket.emit("upload", files[0], (status) => {
        console.log(status);
    });
}

//https://github.com/dropzone/dropzone/wiki/make-the-whole-body-a-dropzone
//https://www.dropzone.dev/bootstrap.html
Dropzone.autoDiscover = false;
$(document).ready(
    setupDropzone()
)

function setupDropzone() {

    dz = new Dropzone(document.body, {
        url: "/",
        // maxFilesize: 1024 * 1024 * 10,
        // thumbnailWidth: 48,
        // thumbnailHeight: 48,
        previewsContainer: "#previews", // Define the container to display the previews
        autoQueue: false, // Make sure the files aren't queued until manually added
        clickable: "#clickable" // Define the element that should be used as click trigger to select files.
    });

    dz.on("addedfile", file => {
        console.log("A file has been added");
        togglePreviews()
    });

    dz.on("removed", file => {
        console.log("A file has been removed");
        togglePreviews()
    });
}

function togglePreviews() {
    var count = $("#previews").children().length;
    if (count > 0) {
        getPreviewsModal().show()
    } else {
        getPreviewsModal().hide()
    }
}

function getPreviewsModal() {
    var previewsModalEl = document.querySelector('#previews-modal')
    var modal = bootstrap.Modal.getOrCreateInstance(previewsModalEl) // Returns a Bootstrap modal instance
    return modal
}


$("#previews-modal-close").click(previewsClose)
$("#previews-modal-close").click(previewsUpload)
function previewsClose() {
    dz.removeAllFiles(true);
    getPreviewsModal().hide()
}

function previewsUpload() {
    //TODO upload files in dz
    getPreviewsModal().hide()
}

function scrollButtonCallback(entries, observer) {
    // The callback will return an array of entries, even if you are only observing a single item
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // Hide button
            $("#scroll-down-button").removeClass('showBtn')
            $("#scroll-down-button").css({
                bottom: $("#form-row").outerHeight()
            });
        } else {
            // Show button
            $("#scroll-down-button").addClass('showBtn')
            $("#scroll-down-button").css({
                bottom: $("#form-row").outerHeight()
            });
        }
    });
}

$("#scroll-down-button").click(scrollToLast)

let pageObserver = new IntersectionObserver(scrollButtonCallback);
let target = document.querySelector("#messages-bottom")
pageObserver.observe(target);   