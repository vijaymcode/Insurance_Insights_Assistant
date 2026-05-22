import React from 'react'
import Chat from './components/Chat'
import SchemaViewer from './components/SchemaViewer'
import { ShieldCheck } from 'lucide-react'

export default function App() {
  return (
    <div className="flex flex-col h-full">
      {/* Top nav */}
      <header className="flex items-center gap-3 px-5 py-3 bg-white border-b border-slate-200 shadow-sm shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-indigo-600 flex items-center justify-center">
          <ShieldCheck size={16} className="text-white" />
        </div>
        <div>
          <h1 className="font-bold text-slate-800 leading-none text-base">Insurance Insights Assistant</h1>
          <p className="text-xs text-slate-400 mt-0.5">Powered by OpenAI · LangChain · SQLite</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-slate-500">Live</span>
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        <SchemaViewer />
        <main className="flex flex-1 min-h-0 min-w-0">
          <Chat />
        </main>
      </div>
    </div>
  )
}
