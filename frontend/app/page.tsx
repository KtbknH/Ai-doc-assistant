'use client';

import { useState, useRef, useEffect } from 'react';

// Types
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  mode?: string;
  timestamp: Date;
}

interface ApiResponse {
  success: boolean;
  data?: {
    answer: string;
    sources: string[];
    mode: string;
    model: string;
  };
  error?: string;
}


const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [useRag, setUseRag] = useState(true);
  const [showSources, setShowSources] = useState<string | null>(null);
  

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const generateId = () => Math.random().toString(36).substring(2, 9);

  const sendMessage = async () => {
    if (!query.trim() || loading) return;

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: query.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    const currentQuery = query;
    setQuery('');

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: currentQuery,
          use_rag: useRag
        })
      });

      const data: ApiResponse = await response.json();

      if (data.success && data.data) {
        const assistantMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: data.data.answer,
          sources: data.data.sources,
          mode: data.data.mode,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {  
        const errorMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: `❌ Erreur: ${data.error || 'Une erreur est survenue'}`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Erreur:', error);
      const errorMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: '❌ Impossible de contacter le serveur. Vérifiez que le backend est lancé.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setLoading(false);
    inputRef.current?.focus();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setShowSources(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-orange-100">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                🤖 AI Doc Assistant
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Powered by Claude (Anthropic) • RAG System
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs font-medium">
                claude-3-haiku
              </span>
              {messages.length > 0 && (
                <button
                  onClick={clearChat}
                  className="text-gray-400 hover:text-gray-600 text-sm"
                >
                  Effacer
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        {/* Toggle RAG */}
        <div className="bg-white rounded-xl shadow-sm border border-orange-100 p-4 mb-6">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-3 cursor-pointer">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={useRag}
                  onChange={(e) => setUseRag(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-orange-500 transition-colors"></div>
                <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
              </div>
              <span className="font-medium text-gray-700">
                Mode RAG {useRag ? 'activé' : 'désactivé'}
              </span>
            </label>
            <span className="text-sm text-gray-500">
              {useRag 
                ? '✅ Recherche dans les documents avant de répondre' 
                : '⚡ Réponse directe de Claude'}
            </span>
          </div>
        </div>

        {/* Zone de messages */}
        <div className="bg-white rounded-xl shadow-sm border border-orange-100 mb-6 overflow-hidden">
          <div className="h-[500px] overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-400">
                <div className="text-6xl mb-4">💬</div>
                <p className="text-lg font-medium">Commencez la conversation</p>
                <p className="text-sm mt-2">
                  Posez une question sur Python, Claude, le RAG ou FastAPI...
                </p>
                <div className="flex flex-wrap gap-2 mt-6 justify-center">
                  {[
                    "Qui a créé Python?",
                    "C'est quoi le RAG?",
                    "Parle-moi de Claude",
                    "C'est quoi FastAPI?"
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => {
                        setQuery(suggestion);
                        inputRef.current?.focus();
                      }}
                      className="px-3 py-2 bg-orange-50 text-orange-700 rounded-lg text-sm hover:bg-orange-100 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-2' : 'order-1'}`}>
                      {/* Avatar */}
                      <div className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 ${
                          msg.role === 'user' 
                            ? 'bg-orange-500 text-white' 
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {msg.role === 'user' ? '👤' : '🤖'}
                        </div>
                        
                        <div className="flex flex-col gap-1">
                          {/* Message */}
                          <div className={`px-4 py-3 rounded-2xl ${
                            msg.role === 'user'
                              ? 'bg-orange-500 text-white rounded-br-md'
                              : 'bg-gray-100 text-gray-800 rounded-bl-md'
                          }`}>
                            <p className="whitespace-pre-wrap">{msg.content}</p>
                          </div>
                          
                          {/* Metadata pour assistant */}
                          {msg.role === 'assistant' && (
                            <div className="flex items-center gap-3 text-xs text-gray-400 px-1">
                              {msg.mode && (
                                <span className={`px-2 py-0.5 rounded ${
                                  msg.mode === 'RAG' 
                                    ? 'bg-green-50 text-green-600' 
                                    : 'bg-blue-50 text-blue-600'
                                }`}>
                                  {msg.mode}
                                </span>
                              )}
                              {msg.sources && msg.sources.length > 0 && (
                                <button
                                  onClick={() => setShowSources(
                                    showSources === msg.id ? null : msg.id
                                  )}
                                  className="hover:text-gray-600 flex items-center gap-1"
                                >
                                  📚 {msg.sources.length} source(s)
                                  <span className="text-[10px]">
                                    {showSources === msg.id ? '▲' : '▼'}
                                  </span>
                                </button>
                              )}
                            </div>
                          )}
                          
                          {/* Sources expandables */}
                          {showSources === msg.id && msg.sources && (
                            <div className="mt-2 p-3 bg-gray-50 rounded-lg text-xs text-gray-600 border border-gray-200">
                              <p className="font-medium mb-2">Sources utilisées:</p>
                              {msg.sources.map((source, i) => (
                                <div key={i} className="mb-2 p-2 bg-white rounded border border-gray-100">
                                  <p className="text-gray-500 line-clamp-3">{source}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Loading indicator */}
                {loading && (
                  <div className="flex justify-start">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm">
                        🤖
                      </div>
                      <div className="px-4 py-3 bg-gray-100 rounded-2xl rounded-bl-md">
                        <div className="flex items-center gap-2">
                          <div className="flex gap-1">
                            <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                            <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                            <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                          </div>
                          <span className="text-gray-500 text-sm">Claude réfléchit...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Input */}
        <div className="bg-white rounded-xl shadow-sm border border-orange-100 p-4">
          <div className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Posez votre question à Claude..."
              disabled={loading}
              className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-all"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !query.trim()}
              className="px-6 py-3 bg-orange-500 text-white rounded-xl font-medium hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>...</span>
                </>
              ) : (
                <>
                  <span>Envoyer</span>
                  <span>→</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-6 text-center text-sm text-gray-400">
          <p>
            Projet RAG avec Claude • 
            <a href="https://github.com" className="text-orange-500 hover:underline ml-1">GitHub</a> • 
            <a href="https://anthropic.com" className="text-orange-500 hover:underline ml-1">Anthropic</a>
          </p>
        </footer>
      </main>
    </div>
  );
}