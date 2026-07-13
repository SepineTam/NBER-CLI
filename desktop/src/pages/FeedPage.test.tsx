import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { FeedPage } from './FeedPage'

describe('FeedPage keyboard shortcuts', () => {
  it('focuses paper search with Command+K', () => {
    render(<FeedPage />)
    const search = screen.getByPlaceholderText('搜索标题、作者或论文编号')

    screen.getByRole('button', { name: '同步最新论文' }).focus()
    fireEvent.keyDown(document, { key: 'k', metaKey: true })

    expect(search).toHaveFocus()
  })
})
