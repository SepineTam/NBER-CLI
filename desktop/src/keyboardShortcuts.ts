import { useEffect } from 'react'

export const PAPER_SEARCH_INPUT_ID = 'paper-search'

export function usePaperSearchShortcuts(openSearch: () => void) {
  useEffect(() => {
    function handleSearchShortcut(event: KeyboardEvent) {
      const hasCommandModifier = event.metaKey || event.ctrlKey
      const isSearchKey = event.key.toLowerCase() === 'f' || event.key.toLowerCase() === 'k'
      if (hasCommandModifier && isSearchKey) {
        event.preventDefault()
        openSearch()
      }
    }

    document.addEventListener('keydown', handleSearchShortcut)
    return () => document.removeEventListener('keydown', handleSearchShortcut)
  }, [openSearch])
}
