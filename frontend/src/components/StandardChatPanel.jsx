import { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import GuessInput from './GuessInput';

export default function StandardChatPanel({
  messages,
  isStreaming,
  lastMessageId,
  onSend,
  onSubmitGuess,
  sessionId,
}) {
  const bottomRef = useRef(null);

  // Auto-scroll to bottom whenever messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const lastMessage = messages[messages.length - 1];
  const showGuessInput =
    !isStreaming &&
    lastMessageId !== null &&
    lastMessage?.role === 'assistant';

  const handleSubmitGuess = (guessText) => onSubmitGuess(guessText, lastMessageId);

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-gray-50">
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-6">
            <div className="h-12 w-12 rounded-full bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center shadow">
              <span className="text-white text-lg font-bold">AI</span>
            </div>
            <p className="text-sm font-medium text-gray-700">Ask anything to get started</p>
            <p className="text-xs text-gray-400 leading-relaxed max-w-xs">
              Chat freely with the AI. After each response, you will be asked whether you noticed anything that might be inaccurate.
            </p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} role={msg.role} content={msg.content} />
        ))}
        <div ref={bottomRef} />
      </div>

      {showGuessInput && (
        <GuessInput
          key={lastMessageId}
          sessionId={sessionId}
          messageId={lastMessageId}
          onSubmit={handleSubmitGuess}
        />
      )}

      <ChatInput onSend={onSend} disabled={isStreaming} />
    </div>
  );
}
