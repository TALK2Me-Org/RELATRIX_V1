import { useState } from 'react'

interface TooltipProps {
  text: string
  children: React.ReactNode
}

export default function Tooltip({ text, children }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="inline-flex items-center"
      >
        {children}
      </div>
      
      {isVisible && (
        <div className="absolute z-50 px-2 py-1.5 text-xs text-white bg-gray-900 rounded shadow-lg whitespace-normal top-full left-1/2 transform -translate-x-1/2 mt-1 pointer-events-none">
          <div className="max-w-xs min-w-[200px]">{text}</div>
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 -mb-1">
            <div className="w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  )
}

export function HelpIcon({ tooltip }: { tooltip: string }) {
  return (
    <Tooltip text={tooltip}>
      <span className="ml-1 inline-flex items-center justify-center w-4 h-4 text-xs text-gray-500 bg-gray-200 rounded-full cursor-help hover:bg-gray-300 hover:text-gray-700 transition-colors">
        ?
      </span>
    </Tooltip>
  )
}