'use strict';
var fileProgress = {};
var s3ProgressDiv = null;
var currProgressPercent = 0;

(() => {
  function parseURL (text) {
    const xml = new window.DOMParser().parseFromString(text, 'text/xml')
    const tag = xml.getElementsByTagName('Key')[0]
    return decodeURI(tag.childNodes[0].nodeValue)
  }

  function addHiddenInput (body, name, form) {
    const key = parseURL(body)
    const input = document.createElement('input')
    input.type = 'hidden'
    input.value = key
    input.name = name
    form.appendChild(input)
  }

  function calculateFileUploadProgress() {
    const keys = Object.keys(fileProgress);
    var loaded = 0, total = 0;
    for (const k of keys) {
      const e = fileProgress[k];
      if (e.lengthComputable) {
        loaded += e.loaded;
        total += e.total;
      }
    }
    if (total === 0) {
      return 0;
    }
    else {
      return Math.round((loaded / total) * 100);
    }
  }

  function calculateProgressAndSetStyle() {
    var percentage = calculateFileUploadProgress();
    if (s3ProgressDiv && currProgressPercent !== percentage) {
      var pctTxt = percentage.toString() + '%';
      // set the text value and progress style, if we found an s3ProgressDiv
      s3ProgressDiv.innerHTML = pctTxt;
      s3ProgressDiv.style.width = pctTxt;
    }
    currProgressPercent = percentage;
  }

  function waitForAllFiles (form) {
    if (window.uploading !== 0) {
      setTimeout(() => {
        waitForAllFiles(form)
      }, 100)
    } else {
      window.HTMLFormElement.prototype.submit.call(form)
    }
  }

  function request (method, url, data, currFilePart) {
    return new Promise((resolve, reject) => {
      const xhr = new window.XMLHttpRequest()
      xhr.open(method, url)
      xhr.onload = () => {
        if (xhr.status === 201) {
          resolve(xhr.responseText)
        } else {
          reject(xhr.statusText)
        }
      }
      xhr.upload.onprogress = (e) => {
        fileProgress[currFilePart] = e
        calculateProgressAndSetStyle();
      }
      xhr.onerror = () => {
        reject(xhr.statusText)
      }
      xhr.send(data)
    })
  }

  function uploadFiles (form, fileInput, name) {
    const url = fileInput.getAttribute('data-url')
    const promises = Array.from(fileInput.files).map((file) => {
      const s3Form = new window.FormData()
      var currFilePart = 0;
      Array.from(fileInput.attributes).forEach(attr => {
        let name = attr.name
        if (name.startsWith('data-fields')) {
          name = name.replace('data-fields-', '')
          s3Form.append(name, attr.value)
        }
      })
      currFilePart += 1;
      s3Form.append('success_action_status', '201')
      s3Form.append('Content-Type', file.type)
      s3Form.append('file', file)
      return request('POST', url, s3Form, currFilePart)
    })
    Promise.all(promises).then((results) => {
      results.forEach((result) => {
        addHiddenInput(result, name, form)
      })

      const input = document.createElement('input')
      input.type = 'hidden'
      input.name = 's3file'
      input.value = fileInput.name
      fileInput.name = ''
      form.appendChild(input)
      window.uploading -= 1
    }, (err) => {
      console.log(err)
      fileInput.setCustomValidity(err)
      fileInput.reportValidity()
    })
  }

  function clickSubmit (e) {
    let submitButton = e.target
    let form = submitButton.closest('form')
    const submitInput = document.createElement('input')
    submitInput.type = 'hidden'
    submitInput.value = submitButton.value || '1'
    submitInput.name = submitButton.name
    form.appendChild(submitInput)
  }

  function uploadS3Inputs (form) {
    window.uploading = 0
    const inputs = form.querySelectorAll('.s3file')
    Array.from(inputs).forEach(input => {
      window.uploading += 1
      uploadFiles(form, input, input.name)
    }
      )
    waitForAllFiles(form)
  }

  document.addEventListener('DOMContentLoaded', () => {
    s3ProgressDiv = document.getElementById("s3UploadFileProgress");
    let forms = Array.from(document.querySelectorAll('.s3file')).map(input => {
      return input.closest('form')
    })
    forms = new Set(forms)
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        e.preventDefault()
        uploadS3Inputs(e.target)
      })
      let submitButtons = form.querySelectorAll('input[type=submit], button[type=submit]')
      Array.from(submitButtons).forEach(submitButton => {
        submitButton.addEventListener('click',  clickSubmit)
      }
      )
    })
  })
})()
