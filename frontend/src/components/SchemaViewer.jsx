import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Database, ChevronDown, ChevronRight, Table2 } from 'lucide-react'

const TYPE_COLOR = {
  INTEGER: 'text-blue-500',
  REAL:    'text-emerald-500',
  TEXT:    'text-amber-500',
  DATE:    'text-purple-500',
}

function typeTag(desc) {
  const first = desc.split(/\s|–/)[0].toUpperCase()
  return TYPE_COLOR[first] ?? 'text-slate-400'
}

function TableNode({ name, info }) {
  const [open, setOpen] = useState(true)

  return (
    <div className="mb-2">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 w-full text-left px-2 py-1.5 rounded-lg hover:bg-slate-100 transition-colors group"
      >
        {open
          ? <ChevronDown size={13} className="text-slate-400 shrink-0" />
          : <ChevronRight size={13} className="text-slate-400 shrink-0" />}
        <Table2 size={13} className="text-brand-500 shrink-0" />
        <span className="font-semibold text-sm text-slate-700 font-mono">{name}</span>
      </button>

      {open && (
        <div className="ml-5 mt-0.5 space-y-0.5">
          <p className="text-xs text-slate-500 italic px-2 pb-1">{info.description}</p>
          {Object.entries(info.columns).map(([col, desc]) => {
            const typeWord = desc.split(/\s|–/)[0]
            return (
              <div key={col} className="flex items-start gap-2 px-2 py-0.5 rounded hover:bg-slate-50">
                <span className={`text-xs font-mono shrink-0 ${typeTag(desc)}`}>{typeWord}</span>
                <span className="text-xs font-mono text-slate-600">{col}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function SchemaViewer() {
  const [schema, setSchema] = useState(null)

  useEffect(() => {
    axios.get('/api/schema').then(r => setSchema(r.data)).catch(() => {})
  }, [])

  return (
    <aside className="w-64 shrink-0 flex flex-col bg-white border-r border-slate-200 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-200 bg-slate-50">
        <Database size={15} className="text-brand-600" />
        <span className="font-semibold text-sm text-slate-700">Schema</span>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-3">
        {schema
          ? Object.entries(schema).map(([name, info]) => (
              <TableNode key={name} name={name} info={info} />
            ))
          : <p className="text-xs text-slate-400 p-2">Loading schema…</p>}
      </div>
    </aside>
  )
}
