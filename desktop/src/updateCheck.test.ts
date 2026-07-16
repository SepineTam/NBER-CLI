import { afterEach, describe, expect, it, vi } from 'vitest'
import { checkForDesktopUpdate, compareVersions, normalizeVersion } from './updateCheck'

describe('desktop update checks', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('normalizes release tags', () => {
    expect(normalizeVersion(' v1.2.3 ')).toBe('1.2.3')
  })

  it('compares semantic versions', () => {
    expect(compareVersions('1.2.4', '1.2.3')).toBe(1)
    expect(compareVersions('1.2.3', '1.2.3')).toBe(0)
    expect(compareVersions('1.2.2', '1.2.3')).toBe(-1)
  })

  it('reports available updates from GitHub releases', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () => ({ tag_name: 'v0.9.0', html_url: 'https://github.com/sepinetam/nber-cli/releases/tag/v0.9.0' }),
    })))

    await expect(checkForDesktopUpdate('0.8.0')).resolves.toMatchObject({
      available: true,
      latestVersion: '0.9.0',
    })
  })
})
