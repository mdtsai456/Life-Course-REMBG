import { describe, it, expect } from 'vitest'
import { validateImageFile } from '../utils/validateImageFile'
import { MAX_FILE_SIZE, ALLOWED_IMAGE_TYPES } from '../constants'

function mockFile({ name = 'test.png', type = 'image/png', size = 1024 } = {}) {
  const file = new File(['x'], name, { type })
  Object.defineProperty(file, 'size', { value: size, configurable: true })
  return file
}

describe('validateImageFile', () => {
  it('returns null for a valid PNG within size limit', () => {
    expect(validateImageFile(mockFile())).toBeNull()
  })

  it('rejects unsupported MIME type', () => {
    const result = validateImageFile(mockFile({ type: 'image/gif' }))
    expect(result).not.toBeNull()
    expect(result.error).toContain('不支援')
  })

  it('accepts files with an empty MIME type', () => {
    expect(validateImageFile(mockFile({ type: '' }))).toBeNull()
  })

  it('rejects oversized file', () => {
    const result = validateImageFile(mockFile({ size: MAX_FILE_SIZE + 1 }))
    expect(result).not.toBeNull()
    expect(result.error).toContain('過大')
  })
})

describe('constants', () => {
  it('MAX_FILE_SIZE is 10 MB', () => {
    expect(MAX_FILE_SIZE).toBe(10 * 1024 * 1024)
  })

  it('ALLOWED_IMAGE_TYPES includes png, jpeg, webp', () => {
    expect(ALLOWED_IMAGE_TYPES).toEqual(
      expect.arrayContaining(['image/png', 'image/jpeg', 'image/webp']),
    )
  })
})
