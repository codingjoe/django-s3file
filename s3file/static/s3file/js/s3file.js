/*
 The MIT License (MIT)

 Copyright (c) 2014 Bradley Griffiths

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
 */
'use strict';

(function () {
  var getCookie = function (name) {
    var value = '; ' + document.cookie
    var parts = value.split('; ' + name + '=')
    if (parts.length === 2) return parts.pop().split(';').shift()
  }

  var request = function (method, url, data, headers, el, showProgress, cb) {
    var req = new window.XMLHttpRequest()
    req.open(method, url, true)

    Object.keys(headers).forEach(function (key) {
      req.setRequestHeader(key, headers[key])
    })

    req.onload = function () {
      cb(req.status, req.responseText)
    }

    req.onerror = req.onabort = function () {
      disableSubmit(false)
      error(el, 'Sorry, failed to upload file.')
    }

    req.upload.onprogress = function (data) {
      progressBar(el, data, showProgress)
    }

    req.send(data)
  }

  var parseURL = function (text) {
    var xml = new window.DOMParser().parseFromString(text, 'text/xml')
    var tag = xml.getElementsByTagName('Key')[0]
    return unescape(tag.childNodes[0].nodeValue)
  }

  var parseJson = function (json) {
    var data
    try { data = JSON.parse(json) } catch (e) { data = null }
    return data
  }

  var progressBar = function (el, data, showProgress) {
    if (data.lengthComputable === false || showProgress === false) return

    var pcnt = Math.round(data.loaded * 100 / data.total)
    var bar = el.querySelector('.progress-bar')

    bar.style.width = pcnt + '%'
    bar.innerHTML = pcnt + '%'
  }

  var error = function (el, msg) {
    el.className = 's3file'
    el.querySelector('input[type="file"]').value = ''
    window.alert(msg)
  }

  var update = function (el, xml) {
    el.querySelector('input[type="hidden"]').value = parseURL(xml)
    el.className = 's3file'
    el.querySelector('.progress-bar').style.width = '0%'
  }

  var concurrentUploads = 0
  var disableSubmit = function (status) {
    var submitRow = document.querySelector('.submit-row')
    if (!submitRow) return

    var buttons = submitRow.querySelectorAll('input[type=submit]')

    if (status === true) concurrentUploads++
    else concurrentUploads--

    [].forEach.call(buttons, function (el) {
      el.disabled = (concurrentUploads !== 0)
    })
  }

  var upload = function (file, data, el) {
    var form = new window.FormData()

    disableSubmit(true)

    if (data === null) return error(el, 'Sorry, could not get upload URL.')

    el.className = 's3file progress-active'
    var url = data['form_action']
    delete data['form_action']

    Object.keys(data).forEach(function (key) {
      form.append(key, data[key])
    })
    form.append('file', file)

    request('POST', url, form, {}, el, true, function (status, xml) {
      disableSubmit(false)
      if (status !== 201) return error(el, 'Sorry, failed to upload to S3.')
      update(el, xml)
    })
  }

  var getUploadURL = function (e) {
    var el = e.target.parentElement
    var file = el.querySelector('input[type="file"]').files[0]
    var url = el.getAttribute('data-policy-url')
    var form = new window.FormData()
    var headers = {'X-CSRFToken': getCookie('csrftoken')}

    form.append('type', file.type)
    form.append('name', file.name)

    request('POST', url, form, headers, el, false, function (status, json) {
      var data = parseJson(json)

      switch (status) {
        case 200:
          upload(file, data, el)
          break
        case 400:
        case 403:
          error(el, data.error)
          break
        default:
          error(el, 'Sorry, could not get upload URL.')
      }
    })
  }

  var addHandlers = function (el) {
    var input = el.querySelector('input[type="file"]')

    input.addEventListener('change', getUploadURL, false)
  }

  document.addEventListener('DOMContentLoaded', function (e) {
    [].forEach.call(document.querySelectorAll('.s3file'), addHandlers)
  })

  document.addEventListener('DOMNodeInserted', function (e) {
    if (e.target.tagName) {
      var el = e.target.querySelector('.s3file')
      if (el) addHandlers(el)
    }
  })
})()
