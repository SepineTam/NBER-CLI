import { describe, expect, it } from 'vitest'
import { CITATION_STYLES, formatCitation } from './citation'
import type { Paper } from './types'

const paper: Paper = {
  paper_id: 'w33942',
  title: 'Global Trade Reallocation and the New Geography of Production',
  authors: ['Laura Alfaro', 'Pol Antràs', 'Davin Chor'],
  date: '2026-07-13',
  abstract: 'Abstract',
  url: 'https://www.nber.org/papers/w33942',
  pdf_url: null,
  published_version: null,
  topic: 'International Trade',
  programs: 'International Trade and Investment',
  is_read: false,
  from_cache: true,
}

describe('citation formatting', () => {
  it('offers all approved citation styles with BibTeX first', () => {
    expect(CITATION_STYLES.map((style) => style.id)).toEqual([
      'bibtex',
      'apa',
      'mla',
      'harvard',
      'chicago',
      'gbt7714',
    ])
  })

  it('formats a complete BibTeX working paper citation', () => {
    const citation = formatCitation('bibtex', paper)

    expect(citation).toContain('@techreport{alfaro2026global')
    expect(citation).toContain('author = {Laura Alfaro and Pol Antràs and Davin Chor}')
    expect(citation).toContain('number = {33942}')
  })

  it.each([
    ['apa', 'Alfaro, L., Antràs, P., & Chor, D. (2026).'],
    ['mla', 'Alfaro, Laura, et al.'],
    ['harvard', "Alfaro, L., Antràs, P. and Chor, D. (2026)"],
    ['chicago', 'Laura Alfaro, Pol Antràs, and Davin Chor. 2026.'],
    ['gbt7714', 'ALFARO L, ANTRÀS P, CHOR D.'],
  ] as const)('formats %s citations', (style, expected) => {
    expect(formatCitation(style, paper)).toContain(expected)
  })

  it('uses the current Chinese national bibliography standard label', () => {
    expect(CITATION_STYLES.find((style) => style.id === 'gbt7714')?.label).toBe(
      'GB/T 7714—2025',
    )
  })
})
