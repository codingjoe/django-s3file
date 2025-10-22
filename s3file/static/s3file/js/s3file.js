/**
 * Parse XML response from AWS S3 and return the file key.
 *
 * @param {string} responseText - XML response form AWS S3.
 * @return {string} - Key from response.
 */
export function getKeyFromResponse (responseText) {
  const xml = new globalThis.DOMParser().parseFromString(responseText, 'text/xml')
  return decodeURI(xml.querySelector('Key').innerHTML)
}

/**
 * Custom element to upload files to AWS S3.
 * Safari-compatible autonomous custom element that wraps a file input.
 *
 * @extends HTMLElement
 */
export class S3FileInput extends globalThis.HTMLElement {
  constructor () {
    super()
    this.keys = []
    this.upload = null
  }

  connectedCallback () {
    // Find or create the input element
    this._input = this.querySelector('input[type="file"]')
    if (!this._input) {
      this._input = document.createElement('input')
      this._input.type = 'file'
      this._syncAttributes()
      this.appendChild(this._input)
    }

    this.form.addEventListener('formdata', this.fromDataHandler.bind(this))
    this.form.addEventListener('submit', this.submitHandler.bind(this), { once: true })
    this.form.addEventListener('upload', this.uploadHandler.bind(this))
    this._input.addEventListener('change', this.changeHandler.bind(this))
  }

  /**
   * Sync attributes from the custom element to the internal input element.
   */
  _syncAttributes () {
    const attrsToSync = ['name', 'accept', 'required', 'multiple', 'disabled', 'id']
    attrsToSync.forEach(attr => {
      if (this.hasAttribute(attr)) {
        this._input.setAttribute(attr, this.getAttribute(attr))
      }
    })
  }

  /**
   * Proxy properties to the internal input element.
   */
  get files () {
    return this._input ? this._input.files : []
  }

  get name () {
    return this._input ? this._input.name : this.getAttribute('name') || ''
  }

  set name (value) {
    if (this._input) {
      this._input.name = value
    }
    this.setAttribute('name', value)
  }

  get form () {
    return this._input ? this._input.form : this.closest('form')
  }

  get validity () {
    return this._input ? this._input.validity : { valid: true }
  }

  get validationMessage () {
    return this._input ? this._input.validationMessage : ''
  }

  setCustomValidity (message) {
    if (this._input) {
      this._input.setCustomValidity(message)
    }
  }

  reportValidity () {
    return this._input ? this._input.reportValidity() : true
  }

  changeHandler () {
    this.keys = []
    this.upload = null
    try {
      this.form.removeEventListener('submit', this.submitHandler.bind(this))
    } catch (error) {
      console.debug(error)
    }
    this.form.addEventListener('submit', this.submitHandler.bind(this), { once: true })
  }

  /**
   * Submit the form after uploading the files to S3.
   *
   * @param {SubmitEvent} event - The submit event.
   * @return {Promise<void>}
   */
  async submitHandler (event) {
    event.preventDefault()
    this.form.dispatchEvent(new window.CustomEvent('upload'))
    await Promise.all(this.form.pendingRquests)
    this.form.requestSubmit(event.submitter)
  }

  uploadHandler () {
    if (this.files.length && !this.upload) {
      this.upload = this.uploadFiles()
      this.form.pendingRquests = this.form.pendingRquests || []
      this.form.pendingRquests.push(this.upload)
    }
  }

  /**
   * Append the file key to the form data.
   *
   * @param {FormDataEvent} event - The formdata event.
   */
  fromDataHandler (event) {
    if (this.keys.length) {
      event.formData.delete(this.name)
      for (const key of this.keys) {
        event.formData.append(this.name, key)
      }
      event.formData.append('s3file', this.name)
      event.formData.set(`${this.name}-s3f-signature`, this.dataset.s3fSignature)
    }
  }

  /**
   * Upload files to AWS S3 and populate the keys array.
   *
   * @return {Promise<void>}
   */
  async uploadFiles () {
    this.keys = []
    for (const file of this.files) {
      const s3Form = new globalThis.FormData()
      for (const attr of this.attributes) {
        let name = attr.name

        if (name.startsWith('data-fields')) {
          name = name.replace('data-fields-', '')
          s3Form.append(name, attr.value)
        }
      }
      s3Form.append('success_action_status', '201')
      s3Form.append('Content-Type', file.type)
      s3Form.append('file', file)
      console.debug('uploading', this.dataset.url, file)
      try {
        const response = await fetch(this.dataset.url, { method: 'POST', body: s3Form })
        if (response.status === 201) {
          this.keys.push(getKeyFromResponse(await response.text()))
        } else {
          this.setCustomValidity(response.statusText)
          this.reportValidity()
        }
      } catch (error) {
        console.error(error)
        this.setCustomValidity(error)
        this.reportValidity()
      }
    }
  }

  /**
   * Called when observed attributes change.
   */
  static get observedAttributes () {
    return ['name', 'accept', 'required', 'multiple', 'disabled', 'id']
  }

  attributeChangedCallback (name, oldValue, newValue) {
    if (this._input && oldValue !== newValue) {
      if (newValue === null) {
        this._input.removeAttribute(name)
      } else {
        this._input.setAttribute(name, newValue)
      }
    }
  }
}

globalThis.customElements.define('s3-file', S3FileInput)
