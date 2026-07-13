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

export function useRefreshShortcut(refreshFeed: () => void) {
  useEffect(() => {
    function handleRefreshShortcut(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'r') {
        event.preventDefault()
        refreshFeed()
      }
    }

    document.addEventListener('keydown', handleRefreshShortcut)
    return () => document.removeEventListener('keydown', handleRefreshShortcut)
  }, [refreshFeed])
}
