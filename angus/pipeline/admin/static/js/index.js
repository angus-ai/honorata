/*
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
*/
$(function() {
    $("#output").hide();
    $("#templates").hide();

    $.ajax({
        type: 'GET',
        url: "/pipes",
        success : function (results) {
            console.log(JSON.parse(results));
            results = JSON.parse(results);
            for (var i = 0; i < results.length; i++) {
                let pipe = results[i];
                console.log(pipe)
                let result = {
                    device: pipe['video'],
                    camera_placement: pipe['placement'],
                    port: pipe['port'],
                    id: pipe['id'],
                    type: pipe['type'],
                    auto_start: pipe['auto_start'],
                    status: pipe['status'],
                    template: pipe['template'],
                    name: pipe['name']
                };

                allStreams.push(result);
                //console.log(allStreams);

                listing(result);
            }


        }
    });

    $.ajax({
        type: 'GET',
        url: "/streams",
        success: function (data) {
            let device;
            if (Object.keys(data).length == 0) {
                $("#video").append(
                    $('<option>', {
                        value: "",
                        text: "No devices available",
                    }).attr('disabled','disabled'));
            } else {
                for(device in data) {
                    device = data[device];
                    console.log(device);
                    $("#video").append(
                        $('<option>', {
                            value: device.index,
                            text: device.device,
                        })
                    );
                }
            }
            $('select').material_select();
        }
    });

    $("#reveal").click(function () {
        $('.modal').modal('open');
    });

    var camtype = "usb";
    $("#camera-type div.ui.buttons button").on('click',function () {
        $('#camera-type div.ui.buttons button').removeClass('positive');
        $(this).addClass('positive');
        camtype = $(this).val();
        isFirstStepComplete();
    });

    var camplace = "front";
    $("#camera-placement button").on('click',function () {
        camplace = ($(this).val()).split(' ')[0];
        $("#camera-placement button").removeClass('positive');
        $(this).addClass('positive');
        isFirstStepComplete();
    });

    function isFirstStepComplete() {
        console.log(camtype);
        if($("#camera-type div.ui.buttons button").hasClass('positive')){
            if($("#cam-usb").hasClass("positive")){
                $('#usb-selected').show();
                $('#ip-selected').hide();
            }
            else if($("#cam-ip").hasClass("positive")){
                $('#usb-selected').hide();
                $('#ip-selected').show();
            }
        }
    }

    $("#form-content").focusout(function () {
        isSecondStepComplete();
    });

    $("select#video").change(function() {
        isSecondStepComplete();
    });

    $("input#ip").on("change paste keyup", function() {
        isSecondStepComplete();
    });

    function isSecondStepComplete(){
        let video_val = $('select#video').val();
        let ip = $('input#ip').val();
        if(video_val || ip){
            $('#btn-next').removeClass('hide');
            console.log('IP:', ip, 'USB :', video_val);
        }
        else
        {
            $("#btn-next").addClass('hide');
        }
    }

    $("#third-form input").focusout(function () {
        isThirdStepComplete();
    });

    $("#third-form input").on("change paste keyup propertychange input", function() {
        isThirdStepComplete();
    });

    function isThirdStepComplete() {
        if($("#client_id").val() !== "" && $("#access_token").val() !== ""){
            $("#btn-ok").removeClass('hide');
        }
        else
            $("#btn-ok").addClass('hide');
    }

    $("#btn-next").on('click',function(){
        $("btn-back").removeClass("hide");
        switch ($('.step.active').attr('id')){
            case "choose-camera-type":
                $("#choose-camera-type").removeClass("active").addClass("disabled");
                $("#form-step").removeClass('disabled').addClass('active');
                $("#form").show();
                $(".first-step").hide();
                $("#btn-back").removeClass('hide');
                $(this).addClass('hide');
                isSecondStepComplete();
                break;
            case "form-step":
                $("#form-step").removeClass("active").addClass('disabled');
                $("#credentials").removeClass('disabled').addClass('active');
                $('#form').hide();
                $("#third").show();
                $("#btn-back").removeClass('hide');
                $(this).addClass('hide');
                isThirdStepComplete();
                break;
        }
    });

    $("#btn-back").on('click',function(){
        switch ($('.step.active').attr('id')){
            case "form-step":
                $("#form-step").removeClass('active').addClass('disabled');
                $("#choose-camera-type").removeClass("disabled").addClass("active");
                $("#form").hide();
                $(".first-step").show();
                $(this).addClass('hide');
                $("#btn-next").removeClass('hide');
                isFirstStepComplete();
                break;
            case "credentials":
                $("#credentials").removeClass('active').addClass('disabled');
                $("#form-step").removeClass("disabled").addClass("active");
                $("#third").hide();
                $("#form").show();
                $("#btn-next").removeClass('hide');
                $("#btn-ok").addClass('hide');
                isSecondStepComplete();
                break;
        }
    });

    $("#btn-ok").on("click", function(e) {
        approuveModal();
    });

    let allStreams = [];

    $('.modal').modal({
        ready: function(modal, trigger) {
            $('#cam-usb').addClass('positive');
            $("#btn-back").addClass('hide');
            $("#btn-ok").addClass('hide');
            $("#btn-next").removeClass('hide');

            isFirstStepComplete()
        },
        complete: function () {
            resetModal();
        }
    });

    function resetModal() {
        $('#form-step').addClass('disabled').removeClass('active');
        $('#credentials').addClass('disabled').removeClass('active');
        $('#choose-camera-type').removeClass('disabled').addClass('active');
        $('#camera-type div.ui.buttons button').removeClass('positive');
        document.getElementById('access_token').value = "";
        document.getElementById('client_id').value = "";
        $("#form").hide();
        $('#third').hide();
        $(".first-step").show();
    }

    function approuveModal(){
        if($("select#video").val() == "" || $("#client_id").val() == "" || $("#access_token").val() ==""){
            alert("You must complet all the fields");
        }
        else
        {
            let video = camtype === 'usb' ? $("select#video").val() : $("input#ip").val();

            let client_id = $("#client_id").val();
            let access_token = $("#access_token").val();
            let fps = 10;
            let placement = camplace;
            let type = camtype;
            let template = pipe_template;

            let data = {
                "video":video,
                "max_fps": fps,
                "client_id": client_id,
                "access_token": access_token,
                "placement" : placement,
                "type": type,
                "template": template
            };

            console.log(data);

            $.ajax({
                type: 'POST',
                url: "/pipes",
                data: JSON.stringify(data),
                success: function (data) {

                    let result = {
                        device: video,
                        camera_placement: camplace,
                        port: data.video_port,
                        id: data.pipe_id,
                        type: camtype,
                        status: "stopped",
                        template: template
                    };

                    console.log('result', result);

                    allStreams.push(result);

                    listing(result);
                    $('.modal').modal("close");
                }
            });
        }
    }

    let allWin = [];

    document.querySelector('body').addEventListener('click', function(event) {
        if ($(event.target).hasClass('btn-stop') || $(event.target).parent().hasClass('btn-stop')) {
            let pid = $(event.target).closest('.item').attr('id');
            $.ajax({
                url: "/pipes/"+pid,
                type: 'PUT',
                data: '{ "status": "stopped" }',
                success: function() {
                    let pipe = allStreams.find(function(p) {
                        return p.id == pid;
                    });
                    let img = $(event.target).closest('.item').find("img");
                    img.addClass('hide');
                    let name = $(event.target).closest('.item').find('.list-port').text();
                    img[0].src = '';
                    $($(event.target)).closest('.item').find(".live-text").text('Show Live');
                    $(event.target).addClass('disabled');
                    $(event.target).parent().addClass('disabled');
                    $($(event.target)).closest('.item').find(".btn-start").removeClass('disabled');
                    $($(event.target)).closest('.item').find(".btn-live").addClass('disabled');
                }
            });
        }
    });

    document.querySelector('body').addEventListener('click', function(event) {
        if ($(event.target).hasClass('btn-start') || $(event.target).parent().hasClass('btn-start')) {
            let pid = $(event.target).closest('.item').attr('id');
            $.ajax({
                url: "/pipes/"+pid,
                type: 'PUT',
                data: '{ "status": "started" }',
                success: function() {
                    let pipe = allStreams.find(function(p) {
                        return p.id == pid;
                    });
                    $(event.target).addClass('disabled');
                    $(event.target).parent().addClass('disabled');
                    // $(event.target).closest('.item').find('i').removeClass('stop').addClass('play');
                    $($(event.target)).closest('.item').find(".btn-stop").removeClass('disabled');
                    $($(event.target)).closest('.item').find(".btn-live").removeClass('disabled');
                }
            });
        }
    });

    document.querySelector('body').addEventListener('click', function(event) {
        if ($(event.target).hasClass('btn-live') || $(event.target).parent().hasClass('btn-live')) {
            let btn = $(event.target);
            let img = btn.closest('.item').find("img");
            let pipe = allStreams.find(function(p) {
                return p.port == img[0].id.split('-')[1];
            });
            if (btn.closest('.item').find("img").hasClass('hide')) {
                btn.find("span").text('Hide Live');
                btn.closest('.item').find("img").removeClass('hide');
                img[0].src = 'http://localhost:' + pipe.port;
            } else {
                $(event.target).find("span").text('Show Live');
                $(event.target).closest('.item').find("img").addClass('hide');
                img[0].src = '';
            }
        }
    });

    document.querySelector('body').addEventListener('click', function(event) {
        if ($(event.target).hasClass('btn-delete')) {
            let pid = $(event.target).closest('.item').attr('id');
            $.ajax({
                url: "/pipes/"+pid,
                type: 'DELETE',
                success: function() {
                    $(event.target).closest('.item').remove();

                }
            });
        }
    });

    $(".or").on("click", function(event) {
        if ($(this)[0].id === "or-type") {
             $('#cam-usb').toggleClass('positive');
             $('#cam-ip').toggleClass('positive');
             camtype = $('#cam-usb').hasClass('positive') ? 'usb' : 'ip';
             isFirstStepComplete();
        }
    });

    var pipe_template = "cloud-audience";

    function openWindow(url, name) {
        let randomTop = Math.floor((Math.random() * screen.height) + 1);
        let randomLeft = Math.floor((Math.random() * screen.width) + 1);
        allWin[name] = window.open(url,name,'width=700,height=500, top='+randomTop+', left='+randomLeft);
        return allWin[name];
    }

    function closeWindow(name) {
        let window = allWin[name];
        if(window) {
            window.close();
            delete allWin[name];
        }
    }

    function setActionButtons(pipe) {
        let start = $('#' + pipe.id).find('.btn-start')[0];
        let stop = $('#' + pipe.id).find('.btn-stop')[0];
        let live = $('#' + pipe.id).find('.btn-live')[0];
        $(live).find("span").text('Show Live');

        if (pipe.status === "stopped") {
            $(start).removeClass('disabled');
            $(stop).addClass('disabled');
            $(live).addClass('disabled');
        } else {
            $(start).addClass('disabled');
            $(stop).removeClass('disabled')
            $(live).removeClass('disabled')
        }
    }

    function editPipeName(pid, name, cb) {
        var body = {
            name: name
        };

        $.ajax({
                url: "/pipes/"+pid,
                type: 'PUT',
                data: JSON.stringify(body),
                success: function(result) {
                    console.log(result);
                    cb(null);
                },
                error: function() {
                    cb("The name already exist");
                }
            });
    }


    function listing(result) {
        let content = document.querySelector('#mytemplate').content;
        content.querySelector(".item").id = result.id;
        // content.querySelector('a.header').href = "localhost:"+result.port;

        let type = content.querySelector('.list-type');
        type.textContent = result.template;

        let device = content.querySelector('.list-device');
        console.log(result.name);
        device.textContent = result.name ? result.name : 'No name';
        if (!result.name) {
            device.style.fontStyle = "italic";
        } else {
            device.style.fontStyle = "normal";
        }

        let card_title = content.querySelector('.inline-editable');
        card_title.id = 'inline-editable-' + result.id;

        let pipe_input = content.querySelector('.edit-pipe-input');
        pipe_input.id = 'edit-pipe-input-' + result.id;
        pipe_input.value = result.name ? result.name : '';

        let pipe_input_save = content.querySelector('.edit-pipe-save');
        pipe_input_save.id = 'edit-pipe-save-' + result.id;

        let pipe_input_cancel = content.querySelector('.edit-pipe-cancel');
        pipe_input_cancel.id = 'edit-pipe-cancel-' + result.id;

        let cam_placement = content.querySelector('.list-placement');
        cam_placement.textContent = result.camera_placement + ' Camera';

        let auto_start = content.querySelector('input[type=checkbox]');
        auto_start.id = 'auto-start-' + result.id;
        auto_start.checked = result.auto_start ? true : false;

        let image = content.querySelector('.live-image');
        image.id = 'image-' + result.port;

        let delete_button = content.querySelector('.btn-delete');
        delete_button.id = 'delete-' + result.id;

        document.querySelector('#pipes').appendChild(document.importNode(content, true));
        document.getElementById(auto_start.id).addEventListener('change', function(e) {
            var self = $(this);
            if (e.target.tagName.toUpperCase() === "LABEL") {
                return;
            }
            var status = $(this).prop('checked');
            self.attr("disabled", true);

            $.ajax({
                url: "/pipes/"+result.id,
                type: 'PUT',
                data: '{ "auto_start": ' + status + '}',
                success: function(result) {
                    self.attr("disabled", false);
                }
            });

        });

        $('#' + card_title.id).hover(
            function() {
                $(this).addClass("editHover");
                $(this).children('.edit-icon').removeClass('hide');
            },
            function() {
                $(this).removeClass("editHover");
                $(this).children('.edit-icon').addClass('hide');
            }
        );

        $('#' + card_title.id).on("click", function(e) {
            $(this).addClass('hide');
            $(this).closest('.item').find('.edit-pipe').removeClass('hide');
        });
        $('#' + pipe_input_cancel.id).on("click", function(e) {
            $(this).parent().addClass('hide');
            $(this).closest('.item').find('.inline-editable').removeClass('hide');
            $(this).closest('.item').find('.edit-pipe-input').val(result.name ? result.name : '');
        });
        $('#' + pipe_input_save.id).on("click", function(e) {
            let new_name = $(this).closest('.item').find('.edit-pipe-input').val();
            var self = this;
            editPipeName(result.id, new_name, function(err) {
                if (err) {
                    $(self).closest('.item').find('.edit-input-error').removeClass('hide');
                } else {
                    result.name = new_name;
                    $(self).parent().addClass('hide');
                    $(self).closest('.item').find('.inline-editable').removeClass('hide');
                    $(self).closest('.item').find('.list-device').text(result.name ? result.name : 'No Name');
                    if (!result.name) {
                        $(self).closest('.item').find('.list-device')[0].style.fontStyle = "italic";
                    } else {
                        $(self).closest('.item').find('.list-device')[0].style.fontStyle = "normal";
                    }
                    $(self).closest('.item').find('.edit-pipe-error').addClass('hide');

                }

            });
        });
        setActionButtons(result);
    };


    $('select').material_select();
    Materialize.updateTextFields();
});
