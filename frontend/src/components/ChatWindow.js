import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { askQuestion } from '../services/api';

const ChatWindow = ({ selectedDocument }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    // Проверяем, выбран ли документ и готов ли он
    if (selectedDocument && selectedDocument.status !== 'indexed') {
      const errorMessage = {
        role: 'assistant',
        content: `Документ "${selectedDocument.name}" ещё не обработан. Текущий статус: ${selectedDocument.status}. Пожалуйста, подождите, пока он проиндексируется.`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setLoading(false);
      return;
    }


    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await askQuestion(
        input,
        selectedDocument?.id,
        5
      );

      console.log('Response received:', response); // Для отладки

      const assistantMessage = {
        role: 'assistant',
        content: response.answer || response.message || "Ответ получен",
        sources: response.sources || [],
        processingTime: response.processing_time_ms,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to get answer:', error);
      const errorMessage = {
        role: 'assistant',
        content: `Ошибка: ${error.response?.data?.detail || error.message}. Проверьте консоль.`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>
          {selectedDocument ? `📄 ${selectedDocument.name}` : '💬 Все документы'}
        </h2>
        {selectedDocument?.status === 'indexed' && (
          <p style={{ fontSize: '12px', color: '#1e7e34', marginTop: '4px' }}>
            ✓ Документ проиндексирован, готов к вопросам
          </p>
        )}
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>💬</div>
            <h3>Начните диалог</h3>
            <p>Загрузите документы и задавайте вопросы по их содержанию</p>
            {selectedDocument && (
              <p style={{ fontSize: '12px', marginTop: '8px', color: '#666' }}>
                Текущий документ: {selectedDocument.name}
              </p>
            )}
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
                
                {msg.sources && msg.sources.length > 0 && (
                  <details className="sources">
                    <summary>📚 Источники ({msg.sources.length})</summary>
                    {msg.sources.map((src, i) => (
                      <div key={i} className="source-item">
                        <div className="source-doc">📄 {src.document_name}</div>
                        <div className="source-text">{src.chunk_text.substring(0, 200)}...</div>
                        {src.relevance_score && (
                          <div style={{ fontSize: '10px', color: '#999', marginTop: '4px' }}>
                            Релевантность: {Math.round(src.relevance_score * 100)}%
                          </div>
                        )}
                      </div>
                    ))}
                  </details>
                )}
                
                {msg.processingTime && (
                  <div className="processing-time">
                    ⏱️ {Math.round(msg.processingTime)} мс
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        
        {loading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="loading"></div>
              <span style={{ marginLeft: '8px', fontSize: '12px', color: '#666' }}>Думаю...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={selectedDocument ? "Задайте вопрос по документу..." : "Загрузите документы для начала диалога"}
          disabled={loading || (!selectedDocument && messages.length === 0)}
          rows={1}
        />
        <button
          className="send-button"
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          Отправить
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;