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
    //TODO filter messages by id
    if ($("#" + message_id).length == 0) {
        let content = ''
        if (msg.attachments) {
            console.log(`message ${msg.id} has attachments ${msg.attachments}`)
            content = `
            <span id="${msg.attachments}" class="btn" onclick="downloadAttachment('${msg.attachments}');">&#128279;&darr;</span>
            <span><img  style='max-width:200px;max-height:200px' id="img-${msg.attachments}" src="" /></span>
            `
            //style='display:block;max-width:200px;max-height:200px'
            //class="img-thumbnail"
        }

        if (msg.message) {
            content = msg.message
        }
        $('#message-holder').append(`
                    <li class="list-group-item" id="${message_id}">
                        <span class="border border-primary rounded p-1">${msg.user_name}</span> ${content}
                    </li>`)
    }
}

function downloadAttachment(id) {
    console.log(`downloading attachment ${id}`)

    $.ajax({
        url: `/download/${id}`,
        context: document.body
    }).done(function (response) {
        
        $(`#${id}`).remove();
        $(`#img-${id}`).attr("src", `data:image/jpeg;base64, ${response}`);
    });

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
// function upload(file){
//     socket.emit("upload-notification", file, (status) => {
//         console.log(status);
//     });
// }

function notifyUpload(file) {
    let user_name = $('input.username').val()
    console.log(`notifying uploaded file ${file} by ${user_name}`)
    socket.emit('data_event', {
        user_name: user_name,
        upload_notification: file
    })
}

//https://github.com/dropzone/dropzone/wiki/make-the-whole-body-a-dropzone
//https://www.dropzone.dev/bootstrap.html
Dropzone.autoDiscover = false;
$(document).ready(
    setupDropzone()
)

function setupDropzone() {
    var previewNode = document.querySelector("#template");
    previewNode.id = "";
    var previewTemplate = previewNode.parentNode.innerHTML;
    previewNode.parentNode.removeChild(previewNode);
    //imperative setup https://docs.dropzone.dev/getting-started/setup/imperative
    dz = new Dropzone(document.body, {
        url: "/upload",
        // maxFilesize: 1024 * 1024 * 10,
        // thumbnailWidth: 48,
        // thumbnailHeight: 48,
        previewTemplate: previewTemplate,
        previewsContainer: "#previews", // Define the container to display the previews
        autoQueue: false, // Make sure the files aren't queued until manually added
        clickable: "#clickable" // Define the element that should be used as click trigger to select files.
    });

    dz.on("addedfile", file => addFile(file));
    dz.on("removedFile", file => removeFile(file));
    dz.on("success", (file, responseText, e) => completeSuccessFile(file, responseText, e));
    dz.on("error", (file, responseText, xhr) => completeErrorFile(file, responseText, xhr));
}

function togglePreviews() {
    var count = $("#previews").children().length;
    if (count > 0) {
        getPreviewsModal().show()
    } else {
        console.log('empty preview > closing')
        getPreviewsModal().hide()
    }
}

function getPreviewsModal() {
    var previewsModalEl = document.querySelector('#previews-modal')
    var modal = bootstrap.Modal.getOrCreateInstance(previewsModalEl) // Returns a Bootstrap modal instance
    return modal
}


$("#previews-modal-upload").click(previewsUploadAll)
$("#previews-modal-close").click(previewsCloseAll)

function addFile(file) {
    console.log(`file "${file.name}" has added`);
    file.previewElement.querySelector(".start-file-upload").onclick = function () { uploadFile(file) };
    togglePreviews()
}

function uploadFile(file) {
    dz.enqueueFile(file);
    file.previewElement.querySelector(".start-file-upload")
}

async function completeSuccessFile(file, responseText, e) {
    console.log(`file "${file.name}" completed successfully with message ${responseText} and e ${e}`);
    await sleep(750)
    file.previewElement.parentNode.removeChild(file.previewElement);
    notifyUpload(responseText)
}

async function completeErrorFile(file, responseText, xhr) {
    //TODO test error
    console.log(`file "${file.name}" completed with an error ${responseText} ${xhr}`);
    await sleep(1500)
    //file.previewElement.parentNode.removeChild(file.previewElement);
}

function removeFile(file) {
    //TODO chekc why this is not called
    console.log(`file "${file.name}" has removed`);
    togglePreviews()
}

function previewsCloseAll() {
    dz.removeAllFiles(true);
    getPreviewsModal().hide()
}

async function previewsUploadAll() {
    console.log('uploading all files')
    dz.enqueueFiles(dz.getFilesWithStatus(Dropzone.ADDED))
    await sleep(750)
    togglePreviews()
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

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

$("#scroll-down-button").click(scrollToLast)

let pageObserver = new IntersectionObserver(scrollButtonCallback);
let target = document.querySelector("#messages-bottom")
pageObserver.observe(target);   