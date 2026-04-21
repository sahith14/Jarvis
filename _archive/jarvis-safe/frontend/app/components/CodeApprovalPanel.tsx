import { PendingEdit } from '@/lib/types';
import DiffViewer from './DiffViewer';

interface CodeApprovalPanelProps {
  edit: PendingEdit;
  onApprove: () => void;
  onReject: () => void;
}

export default function CodeApprovalPanel({ edit, onApprove, onReject }: CodeApprovalPanelProps) {
  return (
    <div className=\"mt-4 border border-yellow-600 rounded-lg p-4 bg-gray-850\">
      <h3 className=\"text-lg font-semibold text-yellow-400 mb-2\">
        Proposed Edit: {edit.path}
      </h3>
      <div className=\"max-h-96 overflow-auto\">
        <DiffViewer oldContent={edit.oldContent} newContent={edit.newContent} />
      </div>
      <div className=\"mt-4 flex gap-3\">
        <button
          onClick={onApprove}
          className=\"px-4 py-2 bg-green-600 hover:bg-green-700 rounded font-medium\"
        >
          Approve & Apply
        </button>
        <button
          onClick={onReject}
          className=\"px-4 py-2 bg-red-600 hover:bg-red-700 rounded font-medium\"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
