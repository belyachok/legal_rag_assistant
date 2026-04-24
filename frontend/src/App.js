import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import { getDocuments, uploadDocument, deleteDocument } from './services/api';
import './styles/App.css';

function App() {
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadDocuments = useCallback(async () => {
    try {
      const data = await getDocuments();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Failed to load documents:', err);
      setError('Failed to load documents');
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleUpload = async (file) => {
    if (uploading) return;
    setUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      await loadDocuments();
      // Автоматически чистим дубликаты
      setTimeout(() => autoCleanDuplicates(), 1000);
    } catch (err) {
      setError('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

   
  const autoCleanDuplicates = useCallback(async () => {
    try {
      const data = await getDocuments();
      const docs = data.documents || [];
      
      // Находим дубликаты по имени файла
      const filesByName = {};
      docs.forEach(doc => {
        if (!filesByName[doc.name]) filesByName[doc.name] = [];
        filesByName[doc.name].push(doc);
      });
      
      // Для каждого имени оставляем один документ (с наибольшим количеством страниц)
      for (const name in filesByName) {
        const duplicates = filesByName[name];
        if (duplicates.length > 1) {
          // Сортируем: сначала те, у которых есть страницы
          duplicates.sort((a, b) => b.pages - a.pages);
          // Удаляем все, кроме первого
          for (let i = 1; i < duplicates.length; i++) {
            await deleteDocument(duplicates[i].id);
            console.log(`Удалён дубликат: ${duplicates[i].id}`);
          }
        }
      }
      
      // Обновляем список
      await loadDocuments();
    } catch (err) {
      console.error('Auto clean failed:', err);
    }
  }, [loadDocuments]);

  const handleDelete = async (id) => {
    try {
      await deleteDocument(id);
      if (selectedDocument?.id === id) {
        setSelectedDocument(null);
      }
      await loadDocuments();
    } catch (err) {
      setError('Delete failed: ' + err.message);
    }
  };

  const handleSelectDocument = (doc) => {
    setSelectedDocument(doc);
  };

  return (
    <div className="app">
      <Sidebar
        documents={documents}
        selectedDocument={selectedDocument}
        onUpload={handleUpload}
        onDelete={handleDelete}
        onSelect={handleSelectDocument}
        loading={loading}
        error={error}
      />
      <ChatWindow selectedDocument={selectedDocument} />
    </div>
  );
}

export default App;