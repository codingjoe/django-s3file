import { test } from "node:test"
import assert from "node:assert"
import { JSDOM } from "jsdom"
import { readFileSync } from "fs"
import { fileURLToPath } from "url"
import { dirname, join } from "path"

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// Read the s3file.js module
const s3fileCode = readFileSync(
  join(__dirname, "../../s3file/static/s3file/js/s3file.js"),
  "utf-8",
)

// Helper to create a DOM environment
function setupDOM() {
  const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
    url: "http://localhost",
  })
  const window = dom.window
  global.window = window
  global.document = window.document
  global.globalThis = {
    ...global,
    DOMParser: window.DOMParser,
    XMLHttpRequest: window.XMLHttpRequest,
    FormData: window.FormData,
    CustomEvent: window.CustomEvent,
    HTMLFormElement: window.HTMLFormElement,
  }
  return dom
}

test("parseURL - extracts key from XML response", async () => {
  setupDOM()

  // Create a mock XML response like S3 returns
  const xmlText = `<?xml version="1.0" encoding="UTF-8"?>
<PostResponse>
  <Location>https://s3.amazonaws.com/bucket/key</Location>
  <Bucket>bucket</Bucket>
  <Key>uploads/file.txt</Key>
  <ETag>"123abc"</ETag>
</PostResponse>`

  // Evaluate the parseURL function from s3file.js
  eval(s3fileCode)

  const result = parseURL(xmlText)
  assert.strictEqual(result, "uploads/file.txt")
})

test("parseURL - handles URL encoded keys", async () => {
  setupDOM()

  const xmlText = `<?xml version="1.0" encoding="UTF-8"?>
<PostResponse>
  <Key>uploads/file%20with%20spaces.txt</Key>
</PostResponse>`

  eval(s3fileCode)

  const result = parseURL(xmlText)
  assert.strictEqual(result, "uploads/file with spaces.txt")
})

test("waitForAllFiles - waits for uploads to complete", async () => {
  setupDOM()

  eval(s3fileCode)

  const form = document.createElement("form")
  globalThis.uploading = 1
  let submitCalled = false

  // Mock the form submit
  const originalSubmit = globalThis.HTMLFormElement.prototype.submit
  globalThis.HTMLFormElement.prototype.submit = () => {
    submitCalled = true
  }

  waitForAllFiles(form)

  // Initially, submit should not be called
  assert.strictEqual(submitCalled, false)

  // Simulate upload completion
  globalThis.uploading = 0

  // Wait for the setTimeout to execute
  await new Promise((resolve) => setTimeout(resolve, 200))

  assert.strictEqual(submitCalled, true)

  globalThis.HTMLFormElement.prototype.submit = originalSubmit
})

test("request - creates XMLHttpRequest and handles progress", async () => {
  setupDOM()

  eval(s3fileCode)

  const form = document.createElement("form")
  const fileInput = document.createElement("input")
  fileInput.type = "file"
  const file = { name: "test.txt", loaded: 0 }

  form.loaded = 0
  fileInput.loaded = 0

  let progressEventFired = false
  form.addEventListener("progress", () => {
    progressEventFired = true
  })

  const mockXhr = {
    status: 201,
    responseText: "<PostResponse><Key>file.txt</Key></PostResponse>",
    upload: {
      onprogress: null,
    },
    onload: null,
    onerror: null,
    open: () => {},
    send: function () {
      // Simulate successful response
      if (this.onload) {
        this.onload()
      }
    },
  }

  // Mock XMLHttpRequest
  globalThis.XMLHttpRequest = class {
    constructor() {
      return mockXhr
    }
  }

  const promise = request(
    "POST",
    "http://example.com",
    new FormData(),
    fileInput,
    file,
    form,
  )

  const result = await promise
  assert.strictEqual(result, mockXhr.responseText)
})

test("request - handles error responses", async () => {
  setupDOM()

  eval(s3fileCode)

  const form = document.createElement("form")
  const fileInput = document.createElement("input")
  fileInput.type = "file"
  const file = { name: "test.txt", loaded: 0 }

  form.loaded = 0
  fileInput.loaded = 0

  const mockXhr = {
    status: 400,
    statusText: "Bad Request",
    responseText: "",
    upload: {
      onprogress: null,
    },
    onload: null,
    onerror: null,
    open: () => {},
    send: function () {
      if (this.onload) {
        this.onload()
      }
    },
  }

  globalThis.XMLHttpRequest = class {
    constructor() {
      return mockXhr
    }
  }

  const promise = request(
    "POST",
    "http://example.com",
    new FormData(),
    fileInput,
    file,
    form,
  )

  try {
    await promise
    assert.fail("Should have thrown an error")
  } catch (err) {
    assert.strictEqual(err, "Bad Request")
  }
})

test("uploadFiles - processes multiple files", async () => {
  setupDOM()

  eval(s3fileCode)

  const form = document.createElement("form")
  form.total = 0
  form.loaded = 0

  const fileInput = document.createElement("input")
  fileInput.type = "file"
  fileInput.setAttribute("data-url", "http://example.com/upload")
  fileInput.setAttribute("data-fields-key", "uploads/${filename}")
  fileInput.setAttribute("data-fields-success_action_status", "201")

  // Create mock files
  const file1 = new File(["content"], "file1.txt", { type: "text/plain" })
  const file2 = new File(["content"], "file2.txt", { type: "text/plain" })

  Object.defineProperty(fileInput, "files", {
    value: [file1, file2],
  })

  globalThis.uploading = 1
  let uploadCalled = false

  const mockXhr = {
    status: 201,
    responseText: "<PostResponse><Key>uploads/file.txt</Key></PostResponse>",
    upload: {
      onprogress: null,
    },
    onload: null,
    onerror: null,
    open: () => {
      uploadCalled = true
    },
    send: function () {
      if (this.onload) {
        this.onload()
      }
    },
  }

  globalThis.XMLHttpRequest = class {
    constructor() {
      return mockXhr
    }
  }

  uploadFiles(form, fileInput, "document")

  // Wait for promises to settle
  await new Promise((resolve) => setTimeout(resolve, 100))

  assert.strictEqual(uploadCalled, true)
  assert.strictEqual(form.total > 0, true)
})

test("clickSubmit - creates hidden input for submit button", async () => {
  setupDOM()

  eval(s3fileCode)

  const form = document.createElement("form")
  const submitButton = document.createElement("button")
  submitButton.type = "submit"
  submitButton.name = "action"
  submitButton.value = "save"
  submitButton.innerText = "Save"

  form.appendChild(submitButton)

  const event = new Event("click")
  Object.defineProperty(event, "currentTarget", { value: submitButton })

  clickSubmit(event)

  const hiddenInputs = form.querySelectorAll("input[type=hidden]")
  assert.strictEqual(hiddenInputs.length, 1)

  const hiddenInput = hiddenInputs[0]
  assert.strictEqual(hiddenInput.name, "action")
  assert.strictEqual(hiddenInput.value, "save")
})

test("clickSubmit - uses default value when button has no value", async () => {
  setupDOM()

  eval(s3fileCode)

  const form = document.createElement("form")
  const submitButton = document.createElement("button")
  submitButton.type = "submit"
  submitButton.name = "action"
  submitButton.innerText = "Submit"

  form.appendChild(submitButton)

  const event = new Event("click")
  Object.defineProperty(event, "currentTarget", { value: submitButton })

  clickSubmit(event)

  const hiddenInput = form.querySelector("input[type=hidden]")
  assert.strictEqual(hiddenInput.value, "1")
})

test("uploadS3Inputs - initializes and processes form inputs", async () => {
  setupDOM()

  eval(s3fileCode)

  const form = document.createElement("form")

  const fileInput = document.createElement("input")
  fileInput.type = "file"
  fileInput.className = "s3file"
  fileInput.name = "document"
  fileInput.setAttribute("data-url", "http://example.com/upload")
  fileInput.setAttribute("data-s3f-signature", "abc123")

  form.appendChild(fileInput)

  Object.defineProperty(fileInput, "files", {
    value: [new File(["test"], "test.txt", { type: "text/plain" })],
  })

  globalThis.uploading = 0

  const mockXhr = {
    status: 201,
    responseText: "<PostResponse><Key>uploads/file.txt</Key></PostResponse>",
    upload: {
      onprogress: null,
    },
    onload: null,
    onerror: null,
    open: () => {},
    send: function () {
      if (this.onload) {
        this.onload()
      }
    },
  }

  globalThis.XMLHttpRequest = class {
    constructor() {
      return mockXhr
    }
  }

  uploadS3Inputs(form)

  await new Promise((resolve) => setTimeout(resolve, 200))

  // Check that hidden inputs were created
  const hiddenInputs = form.querySelectorAll("input[type=hidden]")
  assert.strictEqual(hiddenInputs.length > 0, true)

  // Check for s3file marker input
  const s3fileInput = form.querySelector("input[name=s3file]")
  assert.strictEqual(s3fileInput !== null, true)
  assert.strictEqual(s3fileInput.value, "document")

  // Check for signature input
  const signatureInput = form.querySelector("input[name=document-s3f-signature]")
  assert.strictEqual(signatureInput !== null, true)
  assert.strictEqual(signatureInput.value, "abc123")
})

test("DOM event listener - attaches submit handler to forms", async () => {
  setupDOM()

  // Create form with file input before evaluating the script
  const form = document.createElement("form")
  const fileInput = document.createElement("input")
  fileInput.type = "file"
  fileInput.className = "s3file"
  fileInput.name = "document"
  fileInput.setAttribute("data-url", "http://example.com/upload")
  fileInput.setAttribute("data-s3f-signature", "test123")

  form.appendChild(fileInput)
  document.body.appendChild(form)

  Object.defineProperty(fileInput, "files", {
    value: [],
  })

  // Mock XMLHttpRequest
  globalThis.XMLHttpRequest = class {
    constructor() {
      return {
        status: 201,
        responseText: "<PostResponse><Key>file.txt</Key></PostResponse>",
        upload: { onprogress: null },
        onload: null,
        onerror: null,
        open: () => {},
        send: function () {
          if (this.onload) this.onload()
        },
      }
    }
  }

  let submitPrevented = false

  // Patch to track if submit was prevented
  form.addEventListener("submit", (submitEvent) => {
    if (submitEvent.defaultPrevented) {
      submitPrevented = true
    }
  })

  eval(s3fileCode)

  const submitEvent = new Event("submit", { bubbles: true, cancelable: true })
  form.dispatchEvent(submitEvent)

  await new Promise((resolve) => setTimeout(resolve, 100))

  // The form submission should have been prevented by our handler
  assert.strictEqual(submitEvent.defaultPrevented, true)
})

test("DOM event listener - attaches click handler to submit buttons", async () => {
  setupDOM()

  const form = document.createElement("form")
  const fileInput = document.createElement("input")
  fileInput.type = "file"
  fileInput.className = "s3file"
  fileInput.name = "document"
  fileInput.setAttribute("data-url", "http://example.com/upload")
  fileInput.setAttribute("data-s3f-signature", "test123")

  const submitButton = document.createElement("button")
  submitButton.type = "submit"
  submitButton.name = "action"
  submitButton.value = "submit"

  form.appendChild(fileInput)
  form.appendChild(submitButton)
  document.body.appendChild(form)

  Object.defineProperty(fileInput, "files", {
    value: [],
  })

  eval(s3fileCode)

  // Simulate click
  submitButton.click()

  // Check if hidden input was created
  const hiddenInput = form.querySelector("input[name=action][type=hidden]")
  assert.strictEqual(hiddenInput !== null, true)
})
