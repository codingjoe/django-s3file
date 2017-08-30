'use strict';

(() => {
  function parseURL (text) {
    console.log(text)
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

  function uploadFiles (e, fileInput, name) {
    const url = fileInput.getAttribute('data-s3-url')
    const form = e.target
    const policy = fileInput.getAttribute('data-policy')
    const signature = fileInput.getAttribute('data-signature')
    const AWSAccessKeyId = fileInput.getAttribute('data-AWSAccessKeyId')
    const promises = Array.from(fileInput.files).map((file) => {
      const s3Form = new window.FormData()
      s3Form.append('policy', policy)
      s3Form.append('signature', signature)
      s3Form.append('AWSAccessKeyId', AWSAccessKeyId)
      s3Form.append('success_action_status', '201')
      s3Form.append('Content-Type', file.type)
      s3Form.append('key', fileInput.getAttribute('data-key') + '/' + file.name)
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
      form.appendChild(input)
      fileInput.name = ''
      form.submit()
    }, (err) => {
      console.log(err)
      fileInput.setCustomValidity(err)
      fileInput.reportValidity()
    })
  }

  function addHandlers (fileInput) {
    const form = fileInput.closest('form')
    form.addEventListener('submit', (e) => {
      uploadFiles(e, fileInput, fileInput.name)
      e.preventDefault()
    }, false)
  }

  document.addEventListener('DOMContentLoaded', () => {
    [].forEach.call(document.querySelectorAll('.s3file'), addHandlers)
  })

  document.addEventListener('DOMNodeInserted', (e) => {
    if (e.target.tagName) {
      const el = e.target.querySelector('.s3file')
      if (el) addHandlers(el)
    }
  })
})()
