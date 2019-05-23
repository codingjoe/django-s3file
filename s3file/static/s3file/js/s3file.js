'use strict';

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

  function calculateFileUploadProgress (fileProgress) {
    const keys = Object.keys(fileProgress)
    var loaded = 0
    var total = 0
    for (const k of keys) {
      const e = fileProgress[k]
      if (e.lengthComputable) {
        loaded += e.loaded
        total += e.total
      }
    }
    if (total === 0) {
      return 0
    } else {
      return Math.round((loaded / total) * 100)
    }
  }

  function calculateProgressAndSetStyle (formUpload) {
    const percentage = calculateFileUploadProgress(formUpload.fileProgress)
    if (formUpload.progressBars && formUpload.progressBars.length > 0) {
      formUpload.progressBars.forEach(pb => {
        if (pb && formUpload.currPercentComplete !== percentage) {
          var pctTxt = percentage.toString() + '%'
          // set the text value and progress style
          pb.innerHTML = pctTxt
          pb.style.width = pctTxt
        }
      })
    }
    formUpload.currPercentComplete = percentage
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

  function request (method, url, data, currFilePart, formUpload) {
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
        formUpload.fileProgress[currFilePart] = e
        calculateProgressAndSetStyle(formUpload)
      }
      xhr.onerror = () => {
        reject(xhr.statusText)
      }
      xhr.send(data)
    })
  }

  function uploadFiles (formUpload, fileInput, name) {
    const url = fileInput.getAttribute('data-url')
    var currFilePart = 0
    const promises = Array.from(fileInput.files).map((file) => {
      const s3Form = new window.FormData()
      Array.from(fileInput.attributes).forEach(attr => {
        let name = attr.name
        if (name.startsWith('data-fields')) {
          name = name.replace('data-fields-', '')
          s3Form.append(name, attr.value)
        }
      })
      currFilePart += 1
      s3Form.append('success_action_status', '201')
      s3Form.append('Content-Type', file.type)
      s3Form.append('file', file)
      return request('POST', url, s3Form, currFilePart, formUpload)
    })
    Promise.all(promises).then((results) => {
      results.forEach((result) => {
        addHiddenInput(result, name, formUpload.form)
      })

      const input = document.createElement('input')
      input.type = 'hidden'
      input.name = 's3file'
      input.value = fileInput.name
      fileInput.name = ''
      formUpload.form.appendChild(input)
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

  function uploadS3Inputs (formUpload) {
    window.uploading = 0
    const inputs = formUpload.form.querySelectorAll('.s3file')
    Array.from(inputs).forEach(input => {
      window.uploading += 1
      uploadFiles(formUpload, input, input.name)
    })
    waitForAllFiles(formUpload.form)
  }

  document.addEventListener('DOMContentLoaded', () => {
    let forms = Array.from(document.querySelectorAll('.s3file')).map(input => {
      return input.closest('form')
    })
    forms = new Set(forms)
    forms.forEach(form => {
      const progressBars = form.querySelectorAll('#s3UploadFileProgress')
      form.addEventListener('submit', (e) => {
        e.preventDefault()
        const formUpload = {
          currPercentComplete: 0,
          form: e.target,
          progressBars: progressBars,
          fileProgress: {}
        }
        uploadS3Inputs(formUpload)
      })
      let submitButtons = form.querySelectorAll('input[type=submit], button[type=submit]')
      Array.from(submitButtons).forEach(submitButton => {
        submitButton.addEventListener('click', clickSubmit)
      }
      )
    })
  })
})()
