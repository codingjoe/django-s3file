'use strict';

(function () {
  function parseURL (text) {
    var xml = new window.DOMParser().parseFromString(text, 'text/xml')
    var tag = xml.getElementsByTagName('Key')[0]
    return decodeURI(tag.childNodes[0].nodeValue)
  }

  function waitForAllFiles (form) {
    if (window.uploading !== 0) {
      setTimeout(function () {
        waitForAllFiles(form)
      }, 100)
    } else {
      window.HTMLFormElement.prototype.submit.call(form)
    }
  }

  function request (method, url, data, fileInput, file, form) {
    file.loaded = 0
    return new Promise(function (resolve, reject) {
      var xhr = new window.XMLHttpRequest()
      xhr.open(method, url)

      xhr.onload = function () {
        if (xhr.status === 201) {
          resolve(xhr.responseText)
        } else {
          reject(xhr.statusText)
        }
      }

      xhr.upload.onprogress = function (e) {
        var diff = e.loaded - file.loaded
        form.loaded += diff
        fileInput.loaded += diff
        file.loaded = e.loaded
        var defaultEventData = {
          currentFile: file,
          currentFileName: file.name,
          currentFileProgress: Math.min(e.loaded / e.total, 1),
          originalEvent: e
        }
        form.dispatchEvent(new window.CustomEvent('progress', {
          detail: Object.assign({
            progress: Math.min(form.loaded / form.total, 1),
            loaded: form.loaded,
            total: form.total
          }, defaultEventData)
        }))
        fileInput.dispatchEvent(new window.CustomEvent('progress', {
          detail: Object.assign({
            progress: Math.min(fileInput.loaded / fileInput.total, 1),
            loaded: fileInput.loaded,
            total: fileInput.total
          }, defaultEventData)
        }))
      }

      xhr.onerror = function () {
        reject(xhr.statusText)
      }

      xhr.send(data)
    })
  }

  function uploadFiles (form, fileInput, name) {
    var url = fileInput.getAttribute('data-url')
    fileInput.loaded = 0
    fileInput.total = 0
    var promises = Array.from(fileInput.files).map(function (file) {
      form.total += file.size
      fileInput.total += file.size
      var s3Form = new window.FormData()
      Array.from(fileInput.attributes).forEach(function (attr) {
        var name = attr.name

        if (name.startsWith('data-fields')) {
          name = name.replace('data-fields-', '')
          s3Form.append(name, attr.value)
        }
      })
      s3Form.append('success_action_status', '201')
      s3Form.append('Content-Type', file.type)
      s3Form.append('file', file)
      return request('POST', url, s3Form, fileInput, file, form)
    })
    Promise.all(promises).then(function (results) {
      var keys = results.map(function (result) {
        return parseURL(result)
      })
      var hiddenFileInput = document.createElement('input')
      hiddenFileInput.type = 'hidden'
      hiddenFileInput.name = name
      hiddenFileInput.value = JSON.stringify(keys)
      form.appendChild(hiddenFileInput)
      fileInput.name = ''
      window.uploading -= 1
    }, function (err) {
      console.log(err)
      fileInput.setCustomValidity(err)
      fileInput.reportValidity()
    })
  }

  function clickSubmit (e) {
    var submitButton = e.target
    var form = submitButton.closest('form')
    var submitInput = document.createElement('input')
    submitInput.type = 'hidden'
    submitInput.value = submitButton.value || '1'
    submitInput.name = submitButton.name
    form.appendChild(submitInput)
  }

  function uploadS3Inputs (form) {
    window.uploading = 0
    form.loaded = 0
    form.total = 0
    var inputs = Array.from(form.querySelectorAll('.s3file'))
    var hiddenS3Input = document.createElement('input')
    hiddenS3Input.type = 'hidden'
    hiddenS3Input.name = 's3file'
    form.appendChild(hiddenS3Input)
    hiddenS3Input.value = JSON.stringify(inputs.map(function (input) {
      return input.name
    }))
    inputs.forEach(function (input) {
      window.uploading += 1
      uploadFiles(form, input, input.name)
    })
    waitForAllFiles(form)
  }

  document.addEventListener('DOMContentLoaded', function () {
    var forms = Array.from(document.querySelectorAll('.s3file')).map(function (input) {
      return input.closest('form')
    })
    forms = new Set(forms)
    forms.forEach(function (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault()
        uploadS3Inputs(e.target)
      })
      var submitButtons = form.querySelectorAll('input[type=submit], button[type=submit]')
      Array.from(submitButtons).forEach(function (submitButton) {
        submitButton.addEventListener('click', clickSubmit)
      })
    })
  })
})()
