import { useState, useCallback } from 'react';
import { uploadFiles, type UploadResponse } from '../lib/api';

interface Props {
  onComplete: (result: UploadResponse, restaurantName: string) => void;
  onBack: () => void;
}

export function UploadPage({ onComplete, onBack }: Props) {
  const [name, setName] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const ALLOWED = ['.csv', '.xlsx', '.xls', '.tsv'];

  const addFiles = (newFiles: FileList | File[]) => {
    const valid = Array.from(newFiles).filter((f) => {
      const ext = '.' + f.name.split('.').pop()?.toLowerCase();
      return ALLOWED.includes(ext);
    });
    setFiles((prev) => [...prev, ...valid]);
    setError('');
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }, []);

  const handleSubmit = async () => {
    if (!files.length) {
      setError('Upload at least one file.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const result = await uploadFiles(files, name || 'Restaurant');
      onComplete(result, name || 'Restaurant');
    } catch (e: any) {
      setError(e.message || 'Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center px-6 py-16">
      <div className="max-w-lg w-full">
        <button onClick={onBack} className="text-gray-500 hover:text-white text-sm mb-6 cursor-pointer">
          &larr; Back
        </button>

        <h2 className="text-2xl font-bold mb-2">Upload your exports</h2>
        <p className="text-gray-400 text-sm mb-8">
          Sales reports, labor data, refund logs, menu mix, time cards — whatever you have.
        </p>

        {/* Restaurant name */}
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          Restaurant name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Joe's Grill"
          className="w-full px-4 py-2.5 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-600 mb-6 focus:outline-none focus:border-amber-500"
        />

        {/* Drop zone */}
        <div
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
            dragging ? 'border-amber-400 bg-amber-500/10' : 'border-gray-700 hover:border-gray-500'
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => {
            const input = document.createElement('input');
            input.type = 'file';
            input.multiple = true;
            input.accept = ALLOWED.join(',');
            input.onchange = () => input.files && addFiles(input.files);
            input.click();
          }}
        >
          <div className="text-gray-400 mb-2">
            {dragging ? 'Drop files here' : 'Drag files here or click to browse'}
          </div>
          <div className="text-xs text-gray-600">CSV, XLSX, TSV</div>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="mt-4 space-y-2">
            {files.map((f, i) => (
              <div key={i} className="flex items-center justify-between px-3 py-2 bg-gray-900 rounded-lg text-sm">
                <span className="text-gray-300 truncate mr-3">{f.name}</span>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs text-gray-600">{(f.size / 1024).toFixed(0)} KB</span>
                  <button
                    onClick={() => removeFile(i)}
                    className="text-gray-500 hover:text-red-400 cursor-pointer"
                  >
                    &times;
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={loading || !files.length}
          className={`mt-6 w-full py-3 rounded-lg font-bold text-lg transition-colors cursor-pointer ${
            loading || !files.length
              ? 'bg-gray-800 text-gray-600 cursor-not-allowed'
              : 'bg-amber-500 hover:bg-amber-400 text-black'
          }`}
        >
          {loading ? 'Analyzing...' : `Analyze ${files.length} file${files.length !== 1 ? 's' : ''}`}
        </button>

        <p className="mt-4 text-xs text-gray-600 text-center">
          Files are processed locally and deleted after analysis. We never store your data.
        </p>
      </div>
    </div>
  );
}
