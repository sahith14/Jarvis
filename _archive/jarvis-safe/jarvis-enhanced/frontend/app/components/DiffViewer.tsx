import ReactDiffViewer, { DiffMethod } from "react-diff-viewer-continued";
export default function DiffViewer({ oldContent, newContent }: {oldContent:string;newContent:string}) {
  return (
    <div className="border border-gray-700 rounded overflow-hidden">
      <ReactDiffViewer oldValue={oldContent} newValue={newContent} splitView={true}
        compareMethod={DiffMethod.WORDS}
        styles={{ diffContainer: {background:"transparent"}, diffRemoved: {background:"#3b1e1e"}, diffAdded: {background:"#1e3b1e"} }}/>
    </div>
  );
}
