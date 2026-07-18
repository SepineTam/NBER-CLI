import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TagEditor } from './TagEditor'

describe('TagEditor', () => {
  it('adds, renames, and hides tags', async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined)
    const onRename = vi.fn().mockResolvedValue(undefined)
    const onRemove = vi.fn().mockResolvedValue(undefined)
    render(
      <TagEditor
        paperId="w12345"
        tags={[
          { name: 'Labor Economics', source: 'topic' },
          { name: 'Must Read', source: 'user' },
        ]}
        onAdd={onAdd}
        onRename={onRename}
        onRemove={onRemove}
      />,
    )

    await userEvent.type(screen.getByRole('textbox', { name: '添加标签' }), 'Priority')
    await userEvent.click(screen.getByRole('button', { name: '添加' }))
    expect(onAdd).toHaveBeenCalledWith('w12345', 'Priority')

    await userEvent.click(screen.getByRole('button', { name: '修改标签 Must Read' }))
    const renameInput = screen.getByRole('textbox', { name: '新的标签名称' })
    await userEvent.clear(renameInput)
    await userEvent.type(renameInput, 'Favourite')
    await userEvent.click(screen.getByRole('button', { name: '保存' }))
    expect(onRename).toHaveBeenCalledWith('w12345', 'Must Read', 'Favourite', 'user')

    await userEvent.click(screen.getByRole('button', { name: '删除标签 Labor Economics' }))
    expect(onRemove).toHaveBeenCalledWith('w12345', 'Labor Economics', 'topic')
  })
})
