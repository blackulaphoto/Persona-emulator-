'use client'

import { useState, useRef, useEffect } from 'react'
import { MessageCircle, Send, X } from 'lucide-react'
import { api, type ChatMessage } from '@/lib/api'

interface ChatBoxProps {
  personaId: string
  personaName: string
}

export default function ChatBox({ personaId, personaName }: ChatBoxProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: input.trim()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await api.chatWithPersona(personaId, userMessage.content, messages)
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.message
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: error instanceof Error ? `Error: ${error.message}` : 'Sorry, I had trouble responding. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-moss text-cream p-4 rounded-full shadow-lg hover:bg-sage transition-colors z-50 flex items-center gap-2"
        aria-label="Open chat"
      >
        <MessageCircle size={24} />
        <span className="hidden sm:inline">Chat with {personaName}</span>
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-cream border-2 border-charcoal/20 rounded-2xl shadow-2xl flex flex-col z-50">
      {/* Header */}
      <div className="bg-moss text-cream p-4 rounded-t-2xl flex items-center justify-between">
        <div>
          <h3 className="font-serif text-lg">Chat with {personaName}</h3>
          <p className="text-xs opacity-90">See how personality evolves through conversation</p>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-cream hover:text-charcoal transition-colors"
          aria-label="Close chat"
        >
          <X size={20} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-sage py-8">
            <MessageCircle size={48} className="mx-auto mb-4 opacity-50" />
            <p className="text-sm">Start a conversation to see how {personaName} responds based on their current personality and experiences.</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-moss text-cream'
                    : 'bg-clay/20 text-charcoal'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-clay/20 text-charcoal rounded-lg px-4 py-2">
              <div className="flex gap-1">
                <span className="animate-bounce">.</span>
                <span className="animate-bounce" style={{ animationDelay: '0.1s' }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>.</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="p-4 border-t border-charcoal/10">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 rounded-lg border-2 border-charcoal/10 bg-cream focus:border-moss focus:outline-none"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-moss text-cream p-2 rounded-lg hover:bg-sage transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Send message"
          >
            <Send size={20} />
          </button>
        </div>
        <p className="text-xs text-sage mt-2">
          Responses reflect {personaName}'s current personality, age, and life experiences
        </p>
      </form>
    </div>
  )
}

