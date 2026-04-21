interface Props { messages: {role:string;content:string}[]; }
export default function ActionLog({ messages }: Props) {
  return (
    <div className="bg-gray-900/50 backdrop-blur rounded-xl p-4 h-64 overflow-y-auto font-mono text-sm border border-gray-700">
      {messages.map((m,i)=>(
        <div key={i} className={`mb-1 ${m.role==="user"?"text-blue-300":m.role==="jarvis"?"text-green-300":"text-gray-400"}`}>
          <span className="font-bold">{m.role==="user"?"You":m.role==="jarvis"?"JARVIS":"System"}:</span> {m.content}
        </div>
      ))}
    </div>
  );
}
