import React from 'react';
import ReactMarkdown from 'react-markdown';

const Message = ({ role, content, sources, processingTime }) => {
  return (
    <div className={`message ${role}`}>
      <div className="message-content">
        <ReactMarkdown>{content}</ReactMarkdown>
        
        {sources && sources.length > 0 && (
          <details className="sources">
            <summary>📚 Источники ({sources.length})</summary>
            {sources.map((src, i) => (
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
        
        {processingTime && (
          <div className="processing-time">
            ⏱️ {Math.round(processingTime)} мс
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;