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

  function waitForAllFiles (form) {
    if (window.uploading !== 0) {
      setTimeout(() => {
        waitForAllFiles(form)
      }, 100)
    } else {
      window.HTMLFormElement.prototype.submit.call(form)
    }
  }

  function request (method, url, data) {
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
      Array.from(fileInput.attributes).forEach(attr => {
        let name = attr.name
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
    e.preventDefault()
    let submitButton = e.target
    let form = submitButton.closest('form')
    const submitInput = document.createElement('input')
    submitInput.type = 'hidden'
    submitInput.value = submitButton.value || true
    submitInput.name = submitButton.name
    form.appendChild(submitInput)
    uploadS3Inputs(form)
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
    let forms = Array.from(document.querySelectorAll('.s3file')).map(input => {
      return input.closest('form')
    })
    forms = new Set(forms)
    forms.forEach(form => {
      form.onsubmit = (e) => {
        e.preventDefault()
        uploadS3Inputs(e.target)
      }
      let submitButtons = form.querySelectorAll('input[type=submit], button[type=submit]')
      Array.from(submitButtons).forEach(submitButton => {
        submitButton.onclick = clickSubmit
      }
      )
    })
  })
})()
