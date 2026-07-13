interface IconProps {
  className?: string
}

const iconProps = {
  'aria-hidden': true,
  fill: 'none',
  stroke: 'currentColor',
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  strokeWidth: 1.8,
  viewBox: '0 0 24 24',
}

export function PapersIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <path d="M5 4h14v16H5z" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </svg>
  )
}

export function SettingsIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.4 1a8 8 0 0 0-1.8-1L14.4 3h-4.8l-.4 3.1a8 8 0 0 0-1.8 1l-2.4-1-2 3.4L5.1 11a7 7 0 0 0 0 2L3 14.5l2 3.4 2.4-1a8 8 0 0 0 1.8 1l.4 3.1h4.8l.4-3.1a8 8 0 0 0 1.8-1l2.4 1 2-3.4-2.1-1.5a7 7 0 0 0 .1-1z" />
    </svg>
  )
}

export function SearchIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </svg>
  )
}

export function RefreshIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <path d="M20 11a8 8 0 1 0-2 5.3M20 5v6h-6" />
    </svg>
  )
}

export function EyeIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <path d="M3 12s3-5 9-5 9 5 9 5-3 5-9 5-9-5-9-5z" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  )
}

export function CloseIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <path d="m6 6 12 12M18 6 6 18" />
    </svg>
  )
}

export function CopyIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <rect x="8" y="8" width="11" height="11" rx="2" />
      <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
    </svg>
  )
}

export function ChevronDownIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <path d="m7 9 5 5 5-5" />
    </svg>
  )
}

export function GlobeIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
    </svg>
  )
}

export function FolderIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <path d="M3 6h7l2 2h9v11H3z" />
    </svg>
  )
}

export function DatabaseIcon({ className }: IconProps) {
  return (
    <svg {...iconProps} className={className}>
      <ellipse cx="12" cy="5" rx="8" ry="3" />
      <path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7" />
    </svg>
  )
}
