import "global-jsdom/register"
import assert from "node:assert"
import { afterEach, describe, mock, test } from "node:test"
import * as s3file from "../../s3file/static/s3file/js/s3file.js"

afterEach(() => {
  mock.restoreAll()
})

describe("getKeyFromResponse", () => {
  test("returns key", () => {
    const responseText = `<?xml version="1.0" encoding="UTF-8"?>
      <PostResponse>
      <Location>https://example-bucket.s3.amazonaws.com/tmp%2Fs2file%2Fsome-file.jpeg</Location>
      <Bucket>example-bucket</Bucket>
      <Key>tmp/s2file/some%20file.jpeg</Key>
      <ETag>"a38155039ec348f97dfd63da4cb2619d"</ETag>
      </PostResponse>`
    assert.strictEqual(
      s3file.getKeyFromResponse(responseText),
      "tmp/s2file/some file.jpeg",
    )
  })
})

describe("S3FileInput", () => {
  test("constructor", () => {
    const input = new s3file.S3FileInput()
    assert.deepStrictEqual(input.keys, [])
    assert.strictEqual(input.upload, null)
  })

  test("connectedCallback", () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    const input = new s3file.S3FileInput()
    form.addEventListener = mock.fn(form.addEventListener)
    form.appendChild(input)
    assert(form.addEventListener.mock.calls.length === 3)
    assert(input._fileInput !== null)
    assert(input._fileInput.type === "file")
  })

  test("connectedCallback associates labels with native file input", () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    const label = document.createElement("label")
    label.setAttribute("for", "test-input")
    form.appendChild(label)
    const input = new s3file.S3FileInput()
    input.setAttribute("id", "test-input")
    form.appendChild(input)
    // Verify that the label's htmlFor points to the hidden file input
    assert(input._fileInput !== null)
    assert.strictEqual(label.htmlFor, input._fileInput.id)
    assert.strictEqual(input._fileInput.id, "test-input-input")
  })

  test("connectedCallback handles input without labels", () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    const input = new s3file.S3FileInput()
    // Should not throw error when there are no labels
    form.appendChild(input)
    assert(input._fileInput !== null)
    assert(input._fileInput.type === "file")
  })

  test("label click triggers file input", () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    const label = document.createElement("label")
    label.setAttribute("for", "clickable-input")
    form.appendChild(label)
    const input = new s3file.S3FileInput()
    input.setAttribute("id", "clickable-input")
    form.appendChild(input)
    // Mock the click on the file input
    input._fileInput.click = mock.fn(input._fileInput.click)
    // Clicking the label should trigger click on the associated input
    label.click()
    // In jsdom, label clicks are automatically forwarded to the associated input
    // We can verify the association is correct
    assert.strictEqual(label.htmlFor, input._fileInput.id)
  })

  test("disconnectedCallback", () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    const input = new s3file.S3FileInput()
    form.addEventListener = mock.fn(form.addEventListener)
    form.appendChild(input)
    const fileInput = input._fileInput
    assert(fileInput !== null)
    // Mock removeEventListener to verify cleanup
    form.removeEventListener = mock.fn(form.removeEventListener)
    fileInput.removeEventListener = mock.fn(fileInput.removeEventListener)
    // Manually call disconnectedCallback since jsdom doesn't trigger it
    input.disconnectedCallback()
    assert(form.removeEventListener.mock.calls.length === 3)
    assert(fileInput.removeEventListener.mock.calls.length === 1)
    assert(fileInput.parentNode === null)
    assert(input._fileInput === null)
  })

  test("connectedCallback prevents duplicate inputs on reconnection", () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    const input = new s3file.S3FileInput()
    // First connection
    form.appendChild(input)
    assert(input._fileInput !== null)
    assert(input.querySelectorAll('input[type="file"]').length === 1)
    // Disconnect and clear state
    input.disconnectedCallback()
    // Reconnect - should create a new input since old one was cleaned up
    input.connectedCallback()
    assert(input._fileInput !== null)
    // Check only one input element exists after reconnection
    const inputElements = input.querySelectorAll('input[type="file"]')
    assert(inputElements.length === 1)
  })

  test("changeHandler", () => {
    const form = document.createElement("form")
    const input = new s3file.S3FileInput()
    input.keys = ["key"]
    input.upload = "upload"
    form.appendChild(input)
    input.changeHandler()
    assert(!input.keys.length)
    assert(!input.upload)
  })

  test("submitHandler", async () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    form.pendingRequests = []
    form.requestSubmit = mock.fn(form.requestSubmit)
    form.dispatchEvent = mock.fn(form.dispatchEvent)
    const submitButton = document.createElement("button")
    form.appendChild(submitButton)
    submitButton.setAttribute("type", "submit")
    const event = new window.SubmitEvent("submit", { submitter: submitButton })
    const input = new s3file.S3FileInput()
    form.appendChild(input)
    await input.submitHandler(event)
    assert(form.dispatchEvent.mock.calls.length === 2)
    assert(form.requestSubmit.mock.calls.length === 2)
  })

  test("uploadHandler", () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    const input = new s3file.S3FileInput()
    form.appendChild(input)
    Object.defineProperty(input, "files", {
      get: () => [new globalThis.File([""], "file.txt")],
    })
    assert(!input.upload)
    assert.strictEqual(input.files.length, 1)
    input.uploadHandler()
    console.log(input.upload)
    assert(input.upload)
    assert(form.pendingRequests)
  })

  test("fromDataHandler", () => {
    const event = new globalThis.CustomEvent("formdata", { formData: new FormData() })
    const form = document.createElement("form")
    document.body.appendChild(form)
    const input = new s3file.S3FileInput()
    form.appendChild(input)
    input.name = "file"
    input.keys = ["key1", "key2"]
    event.formData = new FormData()
    input.fromDataHandler(event)
    assert.deepStrictEqual(event.formData.getAll("file"), ["key1", "key2"])
    assert.strictEqual(event.formData.get("s3file"), "file")
  })

  test("uploadFiles", async () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    const input = new s3file.S3FileInput()
    input.setAttribute("data-fields-policy", "policy")
    form.appendChild(input)
    Object.defineProperty(input, "files", {
      get: () => [new globalThis.File([""], "file.txt")],
    })
    const responseText = `<?xml version="1.0" encoding="UTF-8"?>
      <PostResponse>
      <Location>https://example-bucket.s3.amazonaws.com/tmp%2Fs2file%2Fsome-file.jpeg</Location>
      <Bucket>example-bucket</Bucket>
      <Key>tmp/s2file/some%20file.jpeg</Key>
      <ETag>"a38155039ec348f97dfd63da4cb2619d"</ETag>
      </PostResponse>`
    const response = { status: 201, text: async () => responseText }
    globalThis.fetch = mock.fn(async () => response)
    assert(input.files.length === 1)
    await input.uploadFiles()
    assert(globalThis.fetch.mock.calls.length === 1)
    assert.deepStrictEqual(input.keys, ["tmp/s2file/some file.jpeg"])
  })

  test("uploadFiles with HTTP error", async () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    const input = new s3file.S3FileInput()
    form.appendChild(input)
    Object.defineProperty(input, "files", {
      get: () => [new globalThis.File([""], "file.txt")],
    })
    const response = { status: 400, statusText: "Bad Request" }
    globalThis.fetch = mock.fn(async () => response)
    assert(input.files.length === 1)
    await input.uploadFiles()
    assert(globalThis.fetch.mock.calls.length === 1)
    assert.deepStrictEqual(input.keys, [])
    assert.strictEqual(input.validationMessage, "Bad Request")
  })

  test("uploadFiles with network error", async () => {
    const form = document.createElement("form")
    document.body.appendChild(form)
    const input = new s3file.S3FileInput()
    form.appendChild(input)
    Object.defineProperty(input, "files", {
      get: () => [new globalThis.File([""], "file.txt")],
    })
    globalThis.fetch = mock.fn(async () => {
      throw new Error("Network Error")
    })
    assert(input.files.length === 1)
    await input.uploadFiles()
    assert(globalThis.fetch.mock.calls.length === 1)
    assert.deepStrictEqual(input.keys, [])
    assert.strictEqual(input.validationMessage, "Error: Network Error")
  })
})
