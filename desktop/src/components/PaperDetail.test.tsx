import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { PaperDetail } from './PaperDetail'
import type { Paper } from '../types'

vi.mock('@tauri-apps/plugin-opener', () => ({
  openUrl: vi.fn(),
}))

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
})
