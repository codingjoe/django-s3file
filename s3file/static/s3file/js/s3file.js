'use strict';

class S3UploadProgressEmitter {
  constructor () {
    this.formProgressObjs = {}
    this.events = {}
  }
  _addForm (formId, form) {
    this.formProgressObjs[formId] = {
      form: form,
      percentComplete: 0,
      fileUploadProgress: {}
    }
  }
  get (formId) {
    return this.formProgressObjs[formId]
  }
  percentageChangeEventName (formId) {
    return formId + ':upload-percentage-change'
  }
  subscribe (eventName, fn) {
    if (!this.events[eventName]) {
      this.events[eventName] = []
    }
    this.events[eventName].push(fn)
    return () => {
      this.events[eventName] = this.events[eventName].filter(eventFn => fn !== eventFn)
    }
  }
  emit (eventName, data) {
    const event = this.events[eventName]
    if (event) {
      event.forEach(fn => {
        fn(data)
      })
    }
  }
}

let s3FileUploadProgressEmitter = new S3UploadProgressEmitter();

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

  function calculateFileUploadProgress (fileUploadProgress) {
    const keys = Object.keys(fileUploadProgress)
    var loaded = 0
    var total = 0
    for (const k of keys) {
      const e = fileUploadProgress[k]
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

  function calculateProgressAndEmit (formId) {
    const formObj = s3FileUploadProgressEmitter.get(formId)
    const percentage = calculateFileUploadProgress(formObj.fileUploadProgress)
    const shouldEmit = formObj.percentComplete !== percentage
    formObj.percentComplete = percentage
    if (shouldEmit) {
      const eventKey = s3FileUploadProgressEmitter.percentageChangeEventName(formId)
      s3FileUploadProgressEmitter.emit(eventKey, formObj)
    }
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

  function request (method, url, data, currFilePart, formId) {
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
        s3FileUploadProgressEmitter.get(formId).fileUploadProgress[currFilePart] = e
        calculateProgressAndEmit(formId)
      }
      xhr.onerror = () => {
        reject(xhr.statusText)
      }
      xhr.send(data)
    })
  }

  function uploadFiles (formId, fileInput, name) {
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
      return request('POST', url, s3Form, currFilePart, formId)
    })
    Promise.all(promises).then((results) => {
      results.forEach((result) => {
        const formObj = s3FileUploadProgressEmitter.get(formId)
        addHiddenInput(result, name, formObj.form)
      })

      const input = document.createElement('input')
      input.type = 'hidden'
      input.name = 's3file'
      input.value = fileInput.name
      fileInput.name = ''
      s3FileUploadProgressEmitter.get(formId).form.appendChild(input)
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

  function uploadS3Inputs (formId) {
    window.uploading = 0
    const form = s3FileUploadProgressEmitter.get(formId).form
    const inputs = form.querySelectorAll('.s3file')
    Array.from(inputs).forEach(input => {
      window.uploading += 1
      uploadFiles(formId, input, input.name)
    })
    waitForAllFiles(form)
  }

  document.addEventListener('DOMContentLoaded', () => {
    let forms = Array.from(document.querySelectorAll('.s3file')).map(input => {
      return input.closest('form')
    })
    forms = new Set(forms)
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        e.preventDefault()
        const formId = e.target.id
        s3FileUploadProgressEmitter._addForm(formId, e.target)
        uploadS3Inputs(formId)
      })
      let submitButtons = form.querySelectorAll('input[type=submit], button[type=submit]')
      Array.from(submitButtons).forEach(submitButton => {
        submitButton.addEventListener('click', clickSubmit)
      }
      )
    })
  })
})()
