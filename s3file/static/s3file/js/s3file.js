'use strict';

(function () {
  function parseURL (text) {
    var xml = new window.DOMParser().parseFromString(text, 'text/xml')
    var tag = xml.getElementsByTagName('Key')[0]
    return decodeURI(tag.childNodes[0].nodeValue)
  }

  function addHiddenInput (body, name, form) {
    var key = parseURL(body)
    var input = document.createElement('input')
    input.type = 'hidden'
    input.value = key
    input.name = name
    form.appendChild(input)
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

  function request (method, url, data) {
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

      xhr.onerror = function () {
        reject(xhr.statusText)
      }
      xhr.send(data)
    })
  }

  function uploadFiles (form, fileInput, name) {
    var url = fileInput.getAttribute('data-url')
    var promises = Array.from(fileInput.files).map(function (file) {
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
      return request('POST', url, s3Form)
    })
    Promise.all(promises).then(function (results) {
      results.forEach(function (result) {
        addHiddenInput(result, name, form)
      })
      var input = document.createElement('input')
      input.type = 'hidden'
      input.name = 's3file'
      input.value = fileInput.name
      fileInput.name = ''
      form.appendChild(input)
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
    var inputs = form.querySelectorAll('.s3file')
    Array.from(inputs).forEach(function (input) {
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
