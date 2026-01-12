function parseURL(text) {
  const xml = new globalThis.DOMParser().parseFromString(text, "text/xml")
  const tag = xml.getElementsByTagName("Key")[0]
  return decodeURI(tag.childNodes[0].nodeValue)
}

function waitForAllFiles(form) {
  if (globalThis.uploading !== 0) {
    setTimeout(() => {
      waitForAllFiles(form)
    }, 100)
  } else {
    globalThis.HTMLFormElement.prototype.submit.call(form)
  }
}

async function request(method, url, data, fileInput, file, form) {
  file.loaded = 0
  return await new Promise((resolve, reject) => {
    const xhr = new globalThis.XMLHttpRequest()

    xhr.onload = () => {
      if (xhr.status === 201) {
        resolve(xhr.responseText)
      } else {
        reject(xhr.statusText)
      }
    }

    xhr.upload.onprogress = (e) => {
      const diff = e.loaded - file.loaded
      form.loaded += diff
      fileInput.loaded += diff
      file.loaded = e.loaded
      const defaultEventData = {
        currentFile: file,
        currentFileName: file.name,
        currentFileProgress: Math.min(e.loaded / e.total, 1),
        originalEvent: e,
      }
      form.dispatchEvent(
        new globalThis.CustomEvent("progress", {
          detail: Object.assign(
            {
              progress: Math.min(form.loaded / form.total, 1),
              loaded: form.loaded,
              total: form.total,
            },
            defaultEventData,
          ),
        }),
      )
      fileInput.dispatchEvent(
        new globalThis.CustomEvent("progress", {
          detail: Object.assign(
            {
              progress: Math.min(fileInput.loaded / fileInput.total, 1),
              loaded: fileInput.loaded,
              total: fileInput.total,
            },
            defaultEventData,
          ),
        }),
      )
    }

    xhr.onerror = () => {
      reject(xhr.statusText)
    }

    xhr.open(method, url)
    xhr.send(data)
  })
}

function uploadFiles(form, fileInput, name) {
  const url = fileInput.getAttribute("data-url")
  fileInput.loaded = 0
  fileInput.total = 0
  const promises = [...fileInput.files].map((file) => {
    form.total += file.size
    fileInput.total += file.size
    const s3Form = new globalThis.FormData()

    for (const attr of fileInput.attributes) {
      let name = attr.name

      if (name.startsWith("data-fields")) {
        name = name.replace("data-fields-", "")
        s3Form.append(name, attr.value)
      }
    }

    s3Form.append("success_action_status", "201")
    s3Form.append("Content-Type", file.type)
    s3Form.append("file", file)
    return request("POST", url, s3Form, fileInput, file, form)
  })
  Promise.all(promises).then(
    (results) => {
      results.forEach((result) => {
        const hiddenFileInput = document.createElement("input")
        hiddenFileInput.type = "hidden"
        hiddenFileInput.name = name
        hiddenFileInput.value = parseURL(result)
        form.appendChild(hiddenFileInput)
      })
      fileInput.name = ""
      globalThis.uploading -= 1
    },
    (err) => {
      console.error(err)
      fileInput.setCustomValidity(err)
      fileInput.reportValidity()
    },
  )
}

function clickSubmit(e) {
  const submitButton = e.currentTarget
  const form = submitButton.closest("form")
  const submitInput = document.createElement("input")
  submitInput.type = "hidden"
  submitInput.value = submitButton.value || "1"
  submitInput.name = submitButton.name
  form.appendChild(submitInput)
}

function uploadS3Inputs(form) {
  globalThis.uploading = 0
  form.loaded = 0
  form.total = 0
  const inputs = [...form.querySelectorAll("input[type=file].s3file")]

  inputs.forEach((input) => {
    const hiddenS3Input = document.createElement("input")
    hiddenS3Input.type = "hidden"
    hiddenS3Input.name = "s3file"
    hiddenS3Input.value = input.name
    form.appendChild(hiddenS3Input)
    const hiddenSignatureInput = document.createElement("input")
    hiddenSignatureInput.type = "hidden"
    hiddenSignatureInput.name = `${input.name}-s3f-signature`
    hiddenSignatureInput.value = input.dataset.s3fSignature
    form.appendChild(hiddenSignatureInput)
  })
  inputs.forEach((input) => {
    globalThis.uploading += 1
    uploadFiles(form, input, input.name)
  })
  waitForAllFiles(form)
}

document.addEventListener("DOMContentLoaded", () => {
  let forms = [...document.querySelectorAll("input[type=file].s3file")].map((input) => {
    return input.closest("form")
  })
  forms = new Set(forms)
  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault()
      uploadS3Inputs(e.target)
    })
    const submitButtons = form.querySelectorAll(
      "input[type=submit], button[type=submit]",
    )

    for (const submitButton of submitButtons) {
      submitButton.addEventListener("click", clickSubmit)
    }
  })
})
