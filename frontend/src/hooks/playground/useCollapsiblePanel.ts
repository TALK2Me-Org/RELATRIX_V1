import { useState, useCallback } from 'react'

export function useCollapsiblePanel(storageKey: string) {
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem(storageKey) === 'collapsed'
  })

  const toggle = useCallback(() => {
    setCollapsed(prev => {
      const newState = !prev
      localStorage.setItem(storageKey, newState ? 'collapsed' : 'expanded')
      return newState
    })
  }, [storageKey])

  const expand = useCallback(() => {
    setCollapsed(false)
    localStorage.setItem(storageKey, 'expanded')
  }, [storageKey])

  const collapse = useCallback(() => {
    setCollapsed(true)
    localStorage.setItem(storageKey, 'collapsed')
  }, [storageKey])

  return {
    collapsed,
    toggle,
    expand,
    collapse
  }
}