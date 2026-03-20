export default function ChatMessage({ role, content }) {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[75%] rounded-lg px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words ${
          isUser
            ? 'bg-blue-100 text-gray-900'
            : 'bg-gray-100 text-gray-900'
        }`}
      >
        {content || (
          <span className="text-gray-400 italic">
            <span className="animate-pulse">...</span>
          </span>
        )}
      </div>
    </div>
  );
}
