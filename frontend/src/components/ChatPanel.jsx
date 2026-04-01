import { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';

export default function ChatPanel({ messages, isStreaming, onSend }) {
  const bottomRef = useRef(null);

  // Auto-scroll to bottom whenever messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-gray-50">
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-6">
            <div className="h-12 w-12 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center shadow">
              <span className="text-white text-lg font-bold">AI</span>
            </div>
            <p className="text-sm font-medium text-gray-700">Ask anything to get started</p>
            <p className="text-xs text-gray-400 leading-relaxed max-w-xs">
              The AI response will be automatically fact-checked in the right panel.
              Rate each claim before seeing the results.
            </p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} role={msg.role} content={msg.content} />
        ))}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={onSend} disabled={isStreaming} />
    </div>
  );
}
