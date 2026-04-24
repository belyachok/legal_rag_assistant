import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { BeatLoader } from 'react-spinners';


const Sidebar = ({ documents, selectedDocument, onUpload, onDelete, onSelect, loading, error }) => {
  const [uploadingFile, setUploadingFile] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    if (uploadingFile || !acceptedFiles || acceptedFiles.length === 0) return;
    setUploadingFile(true);
    const file = acceptedFiles[0];
    onUpload(file);
    setTimeout(() => setUploadingFile(false), 2000);
  }, [onUpload, uploadingFile]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
      onDrop,
      accept: { 'application/pdf': ['.pdf'] },
      maxFiles: 5,
    });

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'indexed': return 'status-indexed';
      case 'ocr_processing':
      case 'indexing_processing': return 'status-processing';
      case 'ocr_failed':
      case 'indexing_failed': return 'status-error';
      default: return 'status-uploaded';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'indexed': return '✓ Готов';
      case 'ocr_processing': return 'OCR...';
      case 'indexing_processing': return 'Индексация...';
      case 'ocr_failed': return 'Ошибка OCR';
      case 'indexing_failed': return 'Ошибка индексации';
      default: return 'Загружен';
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>📄 Legal RAG Assistant</h1>
        <p>Интеллектуальный помощник юриста</p>
      </div>

      <div className="upload-area">
        <div {...getRootProps()} className="dropzone">
          <input {...getInputProps()} />
          {isDragActive ? (
            <p>📂 Отпустите файлы здесь...</p>
          ) : (
            <>
              <p>📎 Перетащите PDF файлы сюда</p>
              <p className="small">или нажмите для выбора</p>
            </>
          )}
        </div>
        {loading && (
          <div style={{ textAlign: 'center', marginTop: '12px' }}>
            <BeatLoader size={8} color="#1a73e8" />
            <p style={{ fontSize: '12px', marginTop: '8px', color: '#666' }}>Загрузка...</p>
          </div>
        )}
        {error && (
          <div style={{ marginTop: '12px', padding: '8px', background: '#ffebee', borderRadius: '4px', fontSize: '12px', color: '#d32f2f' }}>
            ⚠️ {error}
          </div>
        )}
      </div>

      <div className="documents-list">
        <h3>Документы ({documents.length})</h3>
        {documents.length === 0 ? (
          <p style={{ color: '#999', textAlign: 'center', padding: '20px' }}>Нет загруженных документов</p>
        ) : (
          documents.map(doc => (
            <div
              key={doc.id}
              className={`document-item ${selectedDocument?.id === doc.id ? 'selected' : ''}`}
              onClick={() => onSelect(doc)}
            >
              <div className="doc-name">{doc.name}</div>
              <div className="doc-status">
                <span className={`status-badge ${getStatusBadgeClass(doc.status)}`}>
                  {getStatusText(doc.status)}
                </span>
                <span style={{ fontSize: '10px', color: '#999' }}>
                  {doc.pages > 0 ? `${doc.pages} стр.` : ''}
                </span>
                <button
                  className="doc-delete"
                  onClick={(e) => { e.stopPropagation(); onDelete(doc.id); }}
                  title="Удалить"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Sidebar;