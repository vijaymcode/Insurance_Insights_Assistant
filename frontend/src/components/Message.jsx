import React from 'react'
import { Bot, User, AlertCircle } from 'lucide-react'
import DataTable from './DataTable'
import SqlBlock from './SqlBlock'

export default function Message({ msg }) {
  const isUser = msg.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 px-4">
        <div className="max-w-[75%] bg-brand-600 text-white px-4 py-3 rounded-2xl rounded-tr-sm shadow-sm text-sm leading-relaxed">
          {msg.content}
        </div>
        <div className="shrink-0 w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center mt-0.5">
          <User size={15} className="text-brand-600" />
        </div>
      </div>
    )
  }

  // Thinking / loading state
  if (msg.loading) {
    return (
      <div className="flex gap-3 px-4">
        <div className="shrink-0 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mt-0.5">
          <Bot size={15} className="text-indigo-600" />
        </div>
        <div className="bg-white border border-slate-200 px-4 py-3 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-2">
          <span className="flex gap-1">
            {[0, 1, 2].map(i => (
              <span
                key={i}
                className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </span>
          <span className="text-sm text-slate-400">Analysing…</span>
        </div>
      </div>
    )
  }

  // Error state
  if (msg.error && !msg.content) {
    return (
      <div className="flex gap-3 px-4">
        <div className="shrink-0 w-8 h-8 rounded-full bg-red-100 flex items-center justify-center mt-0.5">
          <AlertCircle size={15} className="text-red-500" />
        </div>
        <div className="bg-red-50 border border-red-200 px-4 py-3 rounded-2xl rounded-tl-sm text-sm text-red-700">
          {msg.error}
        </div>
      </div>
    )
  }

  // Normal assistant response
  return (
    <div className="flex gap-3 px-4">
      <div className="shrink-0 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mt-0.5">
        <Bot size={15} className="text-indigo-600" />
      </div>
      <div className="flex-1 min-w-0 max-w-[85%]">
        <div className="bg-white border border-slate-200 px-4 py-3 rounded-2xl rounded-tl-sm shadow-sm">
          <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
            {msg.content}
          </p>

          {msg.sql && (
            <SqlBlock
              sql={msg.sql}
              explanation={msg.explanation}
              confidence={msg.confidence}
            />
          )}

          {msg.columns?.length > 0 && (
            <DataTable
              columns={msg.columns}
              rows={msg.rows}
              rowCount={msg.rowCount}
            />
          )}
        </div>
      </div>
    </div>
  )
}
