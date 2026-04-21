interface ActionLogProps {
  messages: { role: string; content: string }[];
}

export default function ActionLog({ messages }: ActionLogProps) {
  return (
    <div className=\"bg-gray-800 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm\">
      {messages.map((msg, i) => (
        <div key={i} className={mb-1 }>
          <span className=\"font-bold\">{msg.role === 'user' ? 'You' : msg.role === 'jarvis' ? 'JARVIS' : 'System'}:</span> {msg.content}
        </div>
      ))}
    </div>
  );
}
