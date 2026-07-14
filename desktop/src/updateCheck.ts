const GITHUB_RELEASES_API_URL = 'https://api.github.com/repos/sepinetam/nber-cli/releases/latest'
const GITHUB_RELEASES_URL = 'https://github.com/sepinetam/nber-cli/releases/latest'

export type UpdateCheckResult =
  | {
      available: true
      currentVersion: string
      latestVersion: string
      releaseUrl: string
      notes?: string
    }
  | {
      available: false
      currentVersion: string
      latestVersion: string
      releaseUrl: string
    }

interface GitHubReleaseResponse {
  tag_name?: string
  name?: string
  html_url?: string
  body?: string
  draft?: boolean
  prerelease?: boolean
}

export async function checkForDesktopUpdate(currentVersion = __APP_VERSION__): Promise<UpdateCheckResult> {
  const response = await fetch(GITHUB_RELEASES_API_URL, {
    headers: {
      Accept: 'application/vnd.github+json',
    },
  })

  if (!response.ok) {
    throw new Error(`GitHub release check failed with status ${response.status}`)
  }

  const release = (await response.json()) as GitHubReleaseResponse
  const latestVersion = normalizeVersion(release.tag_name || release.name || '')
  if (!latestVersion) {
    throw new Error('Latest GitHub release does not include a valid version')
  }

  const current = normalizeVersion(currentVersion)
  return {
    available: compareVersions(latestVersion, current) > 0,
    currentVersion: current,
    latestVersion,
    releaseUrl: release.html_url || GITHUB_RELEASES_URL,
    notes: release.body,
  }
}

export function normalizeVersion(version: string): string {
  return version.trim().replace(/^v/i, '')
}

export function compareVersions(left: string, right: string): number {
  const leftParts = parseVersion(left)
  const rightParts = parseVersion(right)
  const length = Math.max(leftParts.length, rightParts.length)

  for (let index = 0; index < length; index += 1) {
    const diff = (leftParts[index] ?? 0) - (rightParts[index] ?? 0)
    if (diff !== 0) {
      return diff > 0 ? 1 : -1
    }
  }

  return 0
}

function parseVersion(version: string): number[] {
  return normalizeVersion(version)
    .split(/[.-]/)
    .map((part) => Number.parseInt(part, 10))
    .filter((part) => Number.isFinite(part))
}
