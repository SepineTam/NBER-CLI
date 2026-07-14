import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { PaperDetail } from './PaperDetail'
import { copyText } from '../citation'
import type { Paper } from '../types'

vi.mock('@tauri-apps/plugin-opener', () => ({
  openUrl: vi.fn(),
}))

vi.mock('../citation', async () => {
  const actual = await vi.importActual<typeof import('../citation')>('../citation')
  return {
    ...actual,
    copyText: vi.fn().mockResolvedValue(undefined),
  }
})

const paper: Paper = {
  paper_id: 'w12345',
  title: 'A Useful Paper',
  authors: ['Ada Lovelace'],
  date: '2026-07-08',
  abstract: 'Detailed abstract',
  url: 'https://www.nber.org/papers/w12345',
  pdf_url: 'https://www.nber.org/system/files/working_papers/w12345/w12345.pdf',
  published_version: null,
  topic: null,
  programs: null,
  is_read: true,
  from_cache: true,
}

describe('PaperDetail', () => {
  it('renders paper detail and toggles read status', async () => {
    const onToggleRead = vi.fn()
    render(
      <PaperDetail
        paperId={paper.paper_id}
        paper={paper}
        error={null}
        loading={false}
        onClose={vi.fn()}
        onRetry={vi.fn()}
        onToggleRead={onToggleRead}
      />,
    )

    expect(screen.getByRole('heading', { name: 'A Useful Paper' })).toBeInTheDocument()
    expect(screen.getByText('Detailed abstract')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: '标记未读' }))

    expect(onToggleRead).toHaveBeenCalledWith('w12345', false)
  })

  it('keeps the drawer open and retries when paper detail loading fails', async () => {
    const onRetry = vi.fn()
    render(
      <PaperDetail
        paperId="w12345"
        paper={null}
        error="network unavailable"
        loading={false}
        onClose={vi.fn()}
        onRetry={onRetry}
        onToggleRead={vi.fn()}
      />,
    )

    expect(screen.getByText('无法获取详情')).toBeInTheDocument()
    expect(screen.getByText('network unavailable')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: '重试' }))

    expect(onRetry).toHaveBeenCalledWith('w12345')
  })

  it('copies BibTeX by default and supports the approved citation menu', async () => {
    render(
      <PaperDetail
        paperId={paper.paper_id}
        paper={paper}
        error={null}
        loading={false}
        onClose={vi.fn()}
        onRetry={vi.fn()}
        onToggleRead={vi.fn()}
      />,
    )

    expect(screen.queryByRole('button', { name: /下载并打开/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '复制 BibTeX' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: '选择引用格式' }))

    expect(screen.getByRole('menuitem', { name: /APA 7th/ })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: /MLA 9th/ })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: /Harvard/ })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: /Chicago 18th/ })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('menuitem', { name: /GB\/T 7714—2025/ }))
    await userEvent.click(screen.getByRole('button', { name: '复制 GB/T 7714—2025' }))

    expect(copyText).toHaveBeenCalledWith(expect.stringContaining('LOVELACE A.'))
  })

  it('closes the citation menu with Escape', async () => {
    render(
      <PaperDetail
        paperId={paper.paper_id}
        paper={paper}
        error={null}
        loading={false}
        onClose={vi.fn()}
        onRetry={vi.fn()}
        onToggleRead={vi.fn()}
      />,
    )
    const citationToggle = screen.getByRole('button', { name: '选择引用格式' })

    await userEvent.click(citationToggle)
    expect(citationToggle).toHaveAttribute('aria-expanded', 'true')

    await userEvent.keyboard('{Escape}')
    expect(citationToggle).toHaveAttribute('aria-expanded', 'false')
  })
})
