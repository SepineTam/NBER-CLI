import type { Paper } from './types'

export type CitationStyle = 'bibtex' | 'apa' | 'mla' | 'harvard' | 'chicago' | 'gbt7714'

interface CitationStyleDefinition {
  id: CitationStyle
  label: string
  note: string
}

export const CITATION_STYLES: CitationStyleDefinition[] = [
  { id: 'bibtex', label: 'BibTeX', note: '默认' },
  { id: 'apa', label: 'APA 7th', note: 'Author–date' },
  { id: 'mla', label: 'MLA 9th', note: 'Humanities' },
  { id: 'harvard', label: 'Harvard', note: 'Author–date' },
  { id: 'chicago', label: 'Chicago 18th', note: 'Notes & bibliography' },
  { id: 'gbt7714', label: 'GB/T 7714—2025', note: '国标' },
]

export function formatCitation(style: CitationStyle, paper: Paper): string {
  const year = paper.date.slice(0, 4)
  const workingPaperNumber = paper.paper_id.replace(/^w/i, '')
  const url = paper.url || `https://www.nber.org/papers/${paper.paper_id}`
  const initialAuthors = paper.authors.map(authorWithInitials)

  if (style === 'apa') {
    return `${joinAuthors(initialAuthors, '&', true)} (${year}). ${paper.title} (NBER Working Paper No. ${workingPaperNumber}). National Bureau of Economic Research. ${url}`
  }

  if (style === 'mla') {
    const first = splitAuthor(paper.authors[0] || 'Unknown Author')
    const authorLine = `${first.family}, ${first.given}${paper.authors.length > 1 ? ', et al.' : '.'}`
    return `${authorLine} “${paper.title}.” NBER Working Paper no. ${workingPaperNumber}, National Bureau of Economic Research, ${year}, ${url}.`
  }

  if (style === 'harvard') {
    return `${joinAuthors(initialAuthors, 'and', false)} (${year}) ‘${paper.title}’, NBER Working Paper ${workingPaperNumber}. Cambridge, MA: National Bureau of Economic Research. Available at: ${url}`
  }

  if (style === 'chicago') {
    return `${joinAuthors(paper.authors, 'and', true)}. ${year}. “${paper.title}.” NBER Working Paper ${workingPaperNumber}. Cambridge, MA: National Bureau of Economic Research. ${url}.`
  }

  if (style === 'gbt7714') {
    const authors = paper.authors.map(gbAuthor).join(', ')
    return `${authors}. ${paper.title}[R/OL]. Cambridge, MA: National Bureau of Economic Research, ${year}[${new Date().toISOString().slice(0, 10)}]. ${url}.`
  }

  return `@techreport{${citationKey(paper)},
  title = {${paper.title}},
  author = {${paper.authors.join(' and ')}},
  institution = {National Bureau of Economic Research},
  type = {Working Paper},
  number = {${workingPaperNumber}},
  year = {${year}},
  url = {${url}}
}`
}

export async function copyText(value: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value)
    return
  } catch {
    const textArea = document.createElement('textarea')
    textArea.value = value
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    textArea.remove()
  }
}

function splitAuthor(author: string): { family: string; given: string } {
  const names = author.trim().split(/\s+/)
  return {
    family: names.pop() || 'Unknown',
    given: names.join(' '),
  }
}

function authorWithInitials(author: string): string {
  const { family, given } = splitAuthor(author)
  const initials = given
    .split(/\s+/)
    .filter(Boolean)
    .map((name) => `${name.charAt(0).toUpperCase()}.`)
    .join(' ')
  return `${family}, ${initials}`
}

function joinAuthors(authors: string[], finalJoiner: string, serialComma: boolean): string {
  if (authors.length === 0) {
    return 'Unknown author'
  }
  if (authors.length === 1) {
    return authors[0]
  }
  if (authors.length === 2) {
    return `${authors[0]} ${finalJoiner} ${authors[1]}`
  }
  const comma = serialComma ? ',' : ''
  return `${authors.slice(0, -1).join(', ')}${comma} ${finalJoiner} ${authors.at(-1)}`
}

function gbAuthor(author: string): string {
  const { family, given } = splitAuthor(author)
  const initials = given
    .split(/\s+/)
    .filter(Boolean)
    .map((name) => name.charAt(0).toUpperCase())
    .join('')
  return `${family.toUpperCase()} ${initials}`
}

function citationKey(paper: Paper): string {
  const firstFamily = splitAuthor(paper.authors[0] || 'Unknown').family
  const plainFamily = firstFamily.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
  const keyword = paper.title.split(/\s+/).find((word) => word.length > 4) || 'paper'
  return `${plainFamily}${paper.date.slice(0, 4)}${keyword}`
    .replace(/[^a-z0-9]/gi, '')
    .toLowerCase()
}
