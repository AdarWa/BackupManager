$(document).ready(function() {
    $('.action-btn').click(function() {
        var action = $(this).attr('data-action');
        const orginalAction = action;
        var backupId = $(this).attr('bkp-id');
        if(action !== "rename") {
            if(!confirm('Are you sure you want to ' + action + ' this backup?')) {
                return;
            }
            action = action + "/" + backupId;
        }else{
            var newName = prompt("Enter new name for the backup");
            if(newName === null || newName === ""){
                alert("Name cannot be empty");
                return;
            }
            if(!newName.endsWith('.tar')) {
                newName += '.tar';
            }
            action = action + "/" + backupId + "/" + newName;
        }
        $.get({
            url: '/backup/' + action,
            beforeSend: function(xhr) {
                xhr.setRequestHeader('Cookie', document.cookie);
                if("restore" === orginalAction){
                    $('#status').text('Restore in progress...');
                    $("#statusMessage").css("display", "block");
                }
            },
            success: function(response) {
                $('#status').text('Restore completed');
                console.log(response);
                if(orginalAction !== "rename")
                    alert("Action "+orginalAction+" was performed successfully on " + backupId);
                location.reload();
            },
            error: function(xhr, status, error) {
            alert('An error occurred: ' + error+ "\n"+JSON.parse(xhr.responseText).detailed);
            }
        });
    });
});