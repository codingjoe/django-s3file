/**
 * Parse XML response from AWS S3 and return the file key.
 *
 * @param {string} responseText - XML response from AWS S3.
 * @return {string} - Key from response.
 */
export function getKeyFromResponse(responseText) {
  const xml = new globalThis.DOMParser().parseFromString(responseText, "text/xml")
  return decodeURI(xml.querySelector("Key").innerHTML)
}

/**
 * Custom element to upload files to AWS S3.
 * Safari-compatible autonomous custom element that acts as a file input.
 *
 * @extends HTMLElement
 */
export class S3FileInput extends globalThis.HTMLElement {
  static passThroughAttributes = ["accept", "required", "multiple", "class", "style"]
  constructor() {
    super()
    this.keys = []
    this.upload = null
    this._files = []
    this._validationMessage = ""
    this._internals = null

    // Try to attach ElementInternals for form participation
    try {
      this._internals = this.attachInternals?.()
    } catch (e) {
      // ElementInternals not supported
    }
  }

  connectedCallback() {
    // Create a hidden file input for the file picker functionality
    this._fileInput = document.createElement("input")
    this._fileInput.type = "file"

    // Sync attributes to hidden input
    this._syncAttributesToHiddenInput()

    // Listen for file selection on hidden input
    this._fileInput.addEventListener("change", () => {
      this._files = this._fileInput.files
      this.dispatchEvent(new Event("change", { bubbles: true }))
      this.changeHandler()
    })

    // Append elements
    this.appendChild(this._fileInput)

    // Setup form event listeners
    this.form?.addEventListener("formdata", this.fromDataHandler.bind(this))
    this.form?.addEventListener("submit", this.submitHandler.bind(this), {
      once: true,
    })
    this.form?.addEventListener("upload", this.uploadHandler.bind(this))
  }

  /**
   * Sync attributes from custom element to hidden input.
   */
  _syncAttributesToHiddenInput() {
    if (!this._fileInput) return

    S3FileInput.passThroughAttributes.forEach((attr) => {
      if (this.hasAttribute(attr)) {
        this._fileInput.setAttribute(attr, this.getAttribute(attr))
      } else {
        this._fileInput.removeAttribute(attr)
      }
    })

    this._fileInput.disabled = this.hasAttribute("disabled")
  }

  /**
   * Implement HTMLInputElement-like properties.
   */
  get files() {
    return this._files
  }

  get type() {
    return "file"
  }

  get name() {
    return this.getAttribute("name") || ""
  }

  set name(value) {
    this.setAttribute("name", value)
  }

  get value() {
    if (this._files && this._files.length > 0) {
      return this._files[0].name
    }
    return ""
  }

  set value(val) {
    // Setting value on file inputs is restricted for security
    if (val === "" || val === null) {
      this._files = []
      if (this._fileInput) {
        this._fileInput.value = ""
      }
    }
  }

  get form() {
    return this._internals?.form || this.closest("form")
  }

  get disabled() {
    return this.hasAttribute("disabled")
  }

  set disabled(value) {
    if (value) {
      this.setAttribute("disabled", "")
    } else {
      this.removeAttribute("disabled")
    }
  }

  get required() {
    return this.hasAttribute("required")
  }

  set required(value) {
    if (value) {
      this.setAttribute("required", "")
    } else {
      this.removeAttribute("required")
    }
  }

  get validity() {
    if (this._internals) {
      return this._internals.validity
    }
    // Create a basic ValidityState-like object
    const isValid = !this.required || (this._files && this._files.length > 0)
    return {
      valid: isValid && !this._validationMessage,
      valueMissing: this.required && (!this._files || this._files.length === 0),
      customError: !!this._validationMessage,
      badInput: false,
      patternMismatch: false,
      rangeOverflow: false,
      rangeUnderflow: false,
      stepMismatch: false,
      tooLong: false,
      tooShort: false,
      typeMismatch: false,
    }
  }

  get validationMessage() {
    return this._validationMessage
  }

  setCustomValidity(message) {
    this._validationMessage = message || ""
    if (this._internals && typeof this._internals.setValidity === "function") {
      if (message) {
        this._internals.setValidity({ customError: true }, message)
      } else {
        this._internals.setValidity({})
      }
    }
  }

  reportValidity() {
    const validity = this.validity
    if (validity && !validity.valid) {
      this.dispatchEvent(new Event("invalid", { bubbles: false, cancelable: true }))
      return false
    }
    return true
  }

  checkValidity() {
    return this.validity.valid
  }

  click() {
    if (this._fileInput) {
      this._fileInput.click()
    }
  }

  changeHandler() {
    this.keys = []
    this.upload = null
    try {
      this.form?.removeEventListener("submit", this.submitHandler.bind(this))
    } catch (error) {
      console.debug(error)
    }
    this.form?.addEventListener("submit", this.submitHandler.bind(this), {
      once: true,
    })
  }

  /**
   * Submit the form after uploading the files to S3.
   *
   * @param {SubmitEvent} event - The submit event.
   * @return {Promise<void>}
   */
  async submitHandler(event) {
    event.preventDefault()
    this.form?.dispatchEvent(new window.CustomEvent("upload"))
    await Promise.all(this.form?.pendingRequests)
    this.form?.requestSubmit(event.submitter)
  }

  uploadHandler() {
    if (this.files.length && !this.upload) {
      this.upload = this.uploadFiles()
      this.form.pendingRequests = this.form?.pendingRequests || []
      this.form.pendingRequests.push(this.upload)
    }
  }

  /**
   * Append the file key to the form data.
   *
   * @param {FormDataEvent} event - The formdata event.
   */
  fromDataHandler(event) {
    if (this.keys.length) {
      event.formData.delete(this.name)
      for (const key of this.keys) {
        event.formData.append(this.name, key)
      }
      event.formData.append("s3file", this.name)
      event.formData.set(`${this.name}-s3f-signature`, this.dataset.s3fSignature)
    }
  }

  /**
   * Upload files to AWS S3 and populate the keys array.
   *
   * @return {Promise<void>}
   */
  async uploadFiles() {
    this.keys = []
    for (const file of this.files) {
      const s3Form = new globalThis.FormData()
      for (const attr of this.attributes) {
        let name = attr.name

        if (name.startsWith("data-fields")) {
          name = name.replace("data-fields-", "")
          s3Form.append(name, attr.value)
        }
      }
      s3Form.append("success_action_status", "201")
      s3Form.append("Content-Type", file.type)
      s3Form.append("file", file)
      console.debug("uploading", this.dataset.url, file)
      try {
        const response = await fetch(this.dataset.url, {
          method: "POST",
          body: s3Form,
        })
        if (response.status === 201) {
          this.keys.push(getKeyFromResponse(await response.text()))
        } else {
          this.setCustomValidity(response.statusText)
          this.reportValidity()
        }
      } catch (error) {
        console.error(error)
        this.setCustomValidity(String(error))
        this.reportValidity()
      }
    }
  }

  /**
   * Called when observed attributes change.
   */
  static get observedAttributes() {
    return this.passThroughAttributes.concat(["name", "id"])
  }

  attributeChangedCallback(name, oldValue, newValue) {
    this._syncAttributesToHiddenInput()
  }

  /**
   * Declare this element as a form-associated custom element.
   */
  static get formAssociated() {
    return true
  }
}

globalThis.customElements.define("s3-file", S3FileInput)
