import React, { useState } from 'react'
import { Code2, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react'

export default function SqlBlock({ sql, explanation, confidence }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  if (!sql) return null

  const copy = () => {
    navigator.clipboard.writeText(sql)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const confidenceColor = {
    high:   'bg-emerald-100 text-emerald-700',
    medium: 'bg-amber-100 text-amber-700',
    low:    'bg-red-100 text-red-700',
  }[confidence] ?? 'bg-slate-100 text-slate-600'

  return (
    <div className="mt-2 rounded-xl border border-slate-200 bg-slate-50 overflow-hidden text-sm">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center justify-between w-full px-3 py-2 hover:bg-slate-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Code2 size={13} className="text-slate-400" />
          <span className="text-xs font-medium text-slate-500">Generated SQL</span>
          <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${confidenceColor}`}>
            {confidence}
          </span>
        </div>
        {open ? <ChevronUp size={13} className="text-slate-400" /> : <ChevronDown size={13} className="text-slate-400" />}
      </button>

      {open && (
        <>
          {explanation && (
            <p className="px-3 py-1.5 text-xs text-slate-500 italic border-t border-slate-200">
              {explanation}
            </p>
          )}
          <div className="relative border-t border-slate-200">
            <pre className="px-3 py-3 text-xs font-mono text-slate-700 overflow-x-auto scrollbar-thin leading-relaxed">
              {sql}
            </pre>
            <button
              onClick={copy}
              className="absolute top-2 right-2 p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
              title="Copy SQL"
            >
              {copied ? <Check size={13} className="text-emerald-500" /> : <Copy size={13} />}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
