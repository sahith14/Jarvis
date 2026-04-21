import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';

interface DiffViewerProps {
  oldContent: string;
  newContent: string;
}

export default function DiffViewer({ oldContent, newContent }: DiffViewerProps) {
  return (
    <div className=\"border border-gray-700 rounded overflow-hidden\">
      <ReactDiffViewer
        oldValue={oldContent}
        newValue={newContent}
        splitView={true}
        compareMethod={DiffMethod.WORDS}
        styles={{
          diffContainer: { background: 'transparent' },
          diffRemoved: { background: '#3b1e1e' },
          diffAdded: { background: '#1e3b1e' },
        }}
      />
    </div>
  );
}
