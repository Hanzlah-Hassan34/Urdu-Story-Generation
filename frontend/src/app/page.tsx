'use client';

import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function Home() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    setMessages((msgs) => [...msgs, { role: 'user', content: input }]);
    setIsGenerating(true);
    let story = '';
    setMessages((msgs) => [...msgs, { role: 'assistant', content: '' }]);
    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prefix: input, maxLength: 500 }),
      });
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                story = data.chunk
                  .replace(/<EOS>/g, '۔')
                  .replace(/<EOP>/g, '\n')
                  .replace(/<EOT>/g, '۔');
                setMessages((msgs) => {
                  const lastUserIdx = msgs.map(m => m.role).lastIndexOf('user');
                  const newMsgs = [...msgs];
                  const aiIdx = lastUserIdx + 1;
                  if (aiIdx < newMsgs.length && newMsgs[aiIdx].role === 'assistant') {
                    newMsgs[aiIdx] = { ...newMsgs[aiIdx], content: story };
                  }
                  return newMsgs;
                });
                if (data.isFinal) break;
              } catch (e) { /* ignore */ }
            }
          }
        }
      }
    } catch (e) {
      setMessages((msgs) => [...msgs, { role: 'assistant', content: '⚠️ کوئی کہانی پیدا نہیں ہو سکی۔' }]);
    } finally {
      setIsGenerating(false);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isGenerating) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Left Sidebar */}
      <div className="w-64 bg-gray-950 border-r border-gray-700 flex flex-col p-4">
        <button className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg mb-8 w-full font-semibold text-white text-sm">
          <span>+</span> New chat
        </button>
        <nav className="flex-1 space-y-2 text-sm text-gray-400">
        </nav>
        <div className="border-t border-gray-700 pt-4 text-xs text-gray-500">
          <p className="p-2">Urdu Story Generator</p>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-gray-900">
        {/* Header */}
        <div className="border-b border-gray-700 px-8 py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-white">Urdu Story Generator</h1>
        </div>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto px-8 py-8 flex flex-col gap-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <h2 className="text-3xl font-bold mb-2 text-white">Urdu Story Generator</h2>
              <p className="text-lg">Enter a starting phrase in Urdu and watch the story unfold!</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`rounded-xl px-4 py-3 max-w-2xl text-lg whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-gray-700 text-white self-end'
                    : 'bg-gray-800 text-gray-100 self-start'
                }`}
                dir="rtl"
              >
                {msg.content}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-700 p-6 bg-gray-900">
          <div className="flex gap-3 max-w-4xl mx-auto">
            <input
              type="text"
              className="flex-1 px-4 py-3 bg-gray-800 text-white border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-600 text-base placeholder-gray-500"
              placeholder="مثلاً: ایک دن..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              dir="rtl"
              disabled={isGenerating}
              autoFocus
            />
            <button
              onClick={handleSend}
              disabled={isGenerating || !input.trim()}
              className="bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-3 rounded-lg font-semibold flex items-center justify-center"
            >
              {isGenerating ? '⏳' : '↑'}
            </button>
          </div>
          <p className="text-xs text-gray-500 text-center mt-2">
            Urdu Story Generator can make mistakes. Check important info.
          </p>
        </div>
      </div>
    </div>
  );
}
