$ ->
  attach = ($fileInput, policy_url, $el) ->
    $fileInput.fileupload
      paramName: "file"
      autoUpload: true
      dataType: "xml"
      fileInput: $fileInput
      dropZone: $fileInput
      add: (e, data) ->
        $(".submit-row input[type=submit]").prop "disabled", true
        $el.attr "class", "s3file progress-active"
        $.ajax
          url: policy_url
          type: "POST"
          data:
            type: data.files[0].type
            name: data.files[0].name
          success: (fields) ->
            $el.find("input[type=hidden]").val fields.key
            data.url = fields.form_action
            delete fields.form_action
            data.formData = fields
            data.submit()
            return

        return

      progress: (e, data) ->
        progress = parseInt(data.loaded / data.total * 100, 10)
        $el.find(".progress-bar").css(width: progress + "%").html progress + "%"
        return

      error: (e, data) ->
        alert "Oops, file upload failed, please try again"
        $el.attr "class", "s3file form-active"
        return

      done: (e, data) ->
        url = $(data.result).find("Location").text().replace(/%2F/g, "/")
        file_name = url.replace(/^.*[\\\/]/, "")
        $el.find(".link").attr("href", url).text file_name
        $el.attr "class", "s3file link-active"
        $el.find(".progress-bar").css width: "0%"
        $(".submit-row input[type=submit]").prop "disabled", false
        return

    return

  setup = (el) ->
    $el = $(el)
    policy_url = $el.data("url")
    id = $el.data("target")
    file_url = $el.find("#"+id).val()
    $fileInput = $el.find("#s3-"+id)
    class_ = (if (file_url is "") then "form-active" else "link-active")
    $el.attr "class", "s3file " + class_
    $el.find(".remove").click (e) ->
      e.preventDefault()
      $el.find("input[type=hidden]").val ""
      $el.attr "class", "s3file form-active"
      return

    attach $fileInput, policy_url, $el
    return

  $(".s3file").each (i, el) ->
    setup el
    return

  $(document).bind "DOMNodeInserted", (e) ->
    elements = $(e.target).find(".s3file")
    setup elements.get(0) if elements.length
    return

  return
