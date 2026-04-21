import { PendingEdit } from "@/lib/types";
import DiffViewer from "./DiffViewer";

export default function CodeApprovalPanel({ edit, onApprove, onReject }: {edit:PendingEdit; onApprove:()=>void; onReject:()=>void}) {
  const dangerColor = edit.dangerLevel === "HIGH" ? "text-red-500 border-red-500" : edit.dangerLevel === "MEDIUM" ? "text-yellow-500 border-yellow-500" : "text-green-500 border-green-500";
  return (
    <div className="mt-4 border border-gray-700 rounded-xl p-5 bg-gray-900/80 backdrop-blur">
      <div className="flex items-center gap-3 mb-3">
        <h3 className="text-xl font-semibold text-blue-300">Proposed Edit: {edit.path}</h3>
        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${dangerColor}`}>⚠ {edit.dangerLevel} RISK</span>
      </div>
      {edit.warnings.length>0 && (
        <div className="mb-3 p-3 bg-yellow-900/20 border border-yellow-700/50 rounded">
          <p className="text-yellow-400 text-sm font-medium">Warnings:</p>
          <ul className="list-disc list-inside text-yellow-300 text-sm">{edit.warnings.map((w,i)=><li key={i}>{w}</li>)}</ul>
        </div>
      )}
      <div className="max-h-96 overflow-auto rounded border border-gray-700">
        <DiffViewer oldContent={edit.oldContent} newContent={edit.newContent} />
      </div>
      <div className="mt-4 flex gap-3">
        <button onClick={onApprove} className="px-5 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 rounded-lg font-medium shadow-lg shadow-green-900/30">Approve & Apply</button>
        <button onClick={onReject} className="px-5 py-2 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 rounded-lg font-medium shadow-lg shadow-red-900/30">Reject</button>
      </div>
    </div>
  );
}
