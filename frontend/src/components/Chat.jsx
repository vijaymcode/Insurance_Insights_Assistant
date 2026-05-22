import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { Send, RotateCcw, Lightbulb } from 'lucide-react'
import Message from './Message'

const SUGGESTIONS = [
  'What is the total claims cost by region?',
  'Show me the loss ratio by policy type.',
  'Which 10 customers have the highest premiums?',
  'How many active policies exist by type?',
  'What percentage of claims are denied?',
  'Average claim amount for auto policies?',
]

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const question = (text ?? input).trim()
    if (!question || loading) return

    setInput('')
    setLoading(true)

    const userMsg = { id: Date.now(), role: 'user', content: question }
    const thinkingMsg = { id: Date.now() + 1, role: 'assistant', loading: true }
    setMessages(prev => [...prev, userMsg, thinkingMsg])

    try {
      const { data } = await axios.post('/api/chat', { message: question })
      const assistantMsg = {
        id:          Date.now() + 2,
        role:        'assistant',
        content:     data.answer ?? '',
        sql:         data.sql,
        explanation: data.explanation,
        columns:     data.columns ?? [],
        rows:        data.rows ?? [],
        rowCount:    data.row_count ?? 0,
        confidence:  data.confidence,
        error:       data.error,
      }
      setMessages(prev => [...prev.slice(0, -1), assistantMsg])
    } catch (err) {
      const errMsg = {
        id:      Date.now() + 2,
        role:    'assistant',
        content: '',
        error:   err.response?.data?.error ?? 'Network error — is the backend running?',
      }
      setMessages(prev => [...prev.slice(0, -1), errMsg])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const reset = async () => {
    await axios.post('/api/reset').catch(() => {})
    setMessages([])
    setInput('')
    inputRef.current?.focus()
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin py-6 space-y-4">
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full gap-6 px-8 text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-indigo-600 flex items-center justify-center shadow-lg">
              <span className="text-2xl">🛡️</span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800 mb-1">Insurance Insights Assistant</h2>
              <p className="text-slate-500 text-sm max-w-sm">
                Ask any business question in plain English. I'll translate it to SQL and give you the answer.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-xl">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="flex items-start gap-2 text-left p-3 rounded-xl bg-white border border-slate-200 hover:border-brand-400 hover:bg-brand-50 transition-colors text-sm text-slate-700 shadow-sm"
                >
                  <Lightbulb size={14} className="text-amber-400 shrink-0 mt-0.5" />
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => <Message key={msg.id} msg={msg} />)}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="flex items-end gap-2 max-w-4xl mx-auto">
          <button
            onClick={reset}
            className="shrink-0 p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            title="Reset conversation"
          >
            <RotateCcw size={16} />
          </button>

          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask a business question about your insurance data…"
              className="w-full resize-none rounded-xl border border-slate-300 focus:border-brand-500 focus:ring-2 focus:ring-brand-100 px-4 py-2.5 pr-12 text-sm text-slate-800 placeholder-slate-400 outline-none transition-all leading-relaxed scrollbar-thin"
              style={{ maxHeight: '120px' }}
              onInput={e => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
              }}
              disabled={loading}
            />
          </div>

          <button
            onClick={() => send()}
            disabled={!input.trim() || loading}
            className="shrink-0 p-2.5 bg-brand-600 hover:bg-brand-700 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl transition-colors"
            title="Send (Enter)"
          >
            <Send size={16} />
          </button>
        </div>
        <p className="text-center text-xs text-slate-400 mt-2">
          Enter to send · Shift+Enter for new line · Queries are read-only
        </p>
      </div>
    </div>
  )
}
