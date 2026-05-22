import React, { useState } from 'react'
import { ChevronDown, ChevronUp, Download } from 'lucide-react'

export default function DataTable({ columns, rows, rowCount }) {
  const [collapsed, setCollapsed] = useState(false)

  if (!columns?.length) return null

  const downloadCSV = () => {
    const header = columns.join(',')
    const body = rows.map(r =>
      columns.map(c => {
        const v = r[c] ?? ''
        return typeof v === 'string' && v.includes(',') ? `"${v}"` : v
      }).join(',')
    ).join('\n')
    const blob = new Blob([header + '\n' + body], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'query_results.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-50 border-b border-slate-200">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
          Results — {rowCount} row{rowCount !== 1 ? 's' : ''}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={downloadCSV}
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-brand-600 transition-colors"
            title="Download CSV"
          >
            <Download size={13} />
            CSV
          </button>
          <button
            onClick={() => setCollapsed(c => !c)}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            {collapsed ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
          </button>
        </div>
      </div>

      {/* Table */}
      {!collapsed && (
        <div className="overflow-x-auto max-h-72 scrollbar-thin">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-slate-100">
              <tr>
                {columns.map(col => (
                  <th
                    key={col}
                    className="px-3 py-2 text-left text-xs font-semibold text-slate-600 whitespace-nowrap border-b border-slate-200"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr
                  key={i}
                  className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}
                >
                  {columns.map(col => (
                    <td
                      key={col}
                      className="px-3 py-1.5 text-slate-700 whitespace-nowrap border-b border-slate-100 font-mono text-xs"
                    >
                      {row[col] === null || row[col] === undefined
                        ? <span className="text-slate-400 italic">null</span>
                        : String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
