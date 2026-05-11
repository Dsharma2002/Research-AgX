'use client';

import { useState } from 'react';
import { Search, Loader2, CheckCircle, ChevronDown, ChevronUp, Download, Microscope, FileText, Activity } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export default function Home() {
  const [topic, setTopic] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [steps, setSteps] = useState([]);
  const [finalReport, setFinalReport] = useState(null);
  const [criticScore, setCriticScore] = useState(null);
  
  const handleRun = async () => {
    if (!topic.trim()) return;
    
    setIsRunning(true);
    setSteps([]);
    setFinalReport(null);
    setCriticScore(null);
    
    try {
      const response = await fetch('http://localhost:8001/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic }),
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let buffer = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        let boundaryIndex;
        while ((boundaryIndex = buffer.indexOf('\n\n')) !== -1) {
          const message = buffer.slice(0, boundaryIndex);
          buffer = buffer.slice(boundaryIndex + 2);
          
          if (message.startsWith('data: ')) {
            const dataStr = message.substring(6);
            if (!dataStr.trim()) continue;

            try {
              const payload = JSON.parse(dataStr);
              
              if (payload.step === 'done') {
                setFinalReport(payload.data.report);
                setCriticScore(payload.data.critic_score);
                setIsRunning(false);
              } else if (payload.step === 'error') {
                setIsRunning(false);
                setSteps(prev => [...prev, payload]);
              } else {
                setSteps(prev => {
                  const existingStepIndex = prev.findIndex(s => s.step === payload.step);
                  if (existingStepIndex >= 0) {
                    const newSteps = [...prev];
                    newSteps[existingStepIndex] = { ...newSteps[existingStepIndex], ...payload };
                    return newSteps;
                  }
                  return [...prev, payload];
                });
              }
            } catch (e) {
              console.error("Error parsing SSE JSON", e);
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setIsRunning(false);
    }
  };

  const handleDownload = () => {
    if (!finalReport) return;
    const blob = new Blob([finalReport], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${topic.substring(0, 40).replace(/\\s+/g, '_')}_report.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <main className="container">
      <header>
        <h1>
          <Microscope size={40} style={{ marginRight: '10px', color: '#60a5fa' }} />
          Research AGX
        </h1>
        <p className="subtitle">A multi-agent research pipeline: Search → Scrape → Write → Critique</p>
      </header>

      <div className="search-container">
        <input 
          type="text" 
          className="search-input"
          placeholder="e.g. Impact of AI on healthcare in 2025" 
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !isRunning && handleRun()}
        />
        <button 
          className="search-button" 
          onClick={handleRun}
          disabled={isRunning || !topic.trim()}
        >
          {isRunning ? <Loader2 className="spinner" size={20} /> : <Search size={20} />}
          {isRunning ? 'Processing...' : 'Run Pipeline'}
        </button>
      </div>

      {steps.length > 0 && (
        <div className="stepper">
          {steps.map((step, idx) => (
            <StepItem key={idx} step={step} />
          ))}
        </div>
      )}

      {finalReport && (
        <div className="report-container">
          <div className="report-header">
            <h2 className="report-title">
              <FileText size={24} /> Research Report
            </h2>
            <button className="download-btn" onClick={handleDownload}>
              <Download size={18} /> Download
            </button>
          </div>
          <div className="markdown-body">
            <ReactMarkdown>{finalReport}</ReactMarkdown>
          </div>
          
          {criticScore && (
            <div className="critic-review">
              <h3><Activity size={20} /> Critic's Review</h3>
              <div className="markdown-body">
                <ReactMarkdown>{criticScore}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  );
}

function StepItem({ step }) {
  const [expanded, setExpanded] = useState(false);
  
  const hasDataToExpand = step.data && (step.step === 'search' || step.step === 'scrape');
  const dataLabel = step.step === 'search' ? 'Search Results' : 'Scraped Content';

  return (
    <div className="step-item">
      <div className="step-header">
        <div className="step-status-icon">
          {step.status === 'running' ? (
            <Loader2 className="spinner" size={20} />
          ) : step.status === 'failed' ? (
            <span style={{ color: '#ef4444' }}>❌</span>
          ) : (
            <CheckCircle className="check-icon" size={20} />
          )}
        </div>
        <span>{step.label || `Step ${step.step} - ${step.status}`}</span>
      </div>
      
      {hasDataToExpand && step.status === 'complete' && (
        <>
          <button className="accordion-toggle" onClick={() => setExpanded(!expanded)}>
            <span>{dataLabel}</span>
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          {expanded && (
            <div className="accordion-content">
              {typeof step.data === 'string' ? step.data : JSON.stringify(step.data, null, 2)}
            </div>
          )}
        </>
      )}
    </div>
  );
}
