import React, { useState, useEffect, useRef } from 'react';
import { 
  UploadCloud, 
  Play, 
  Terminal, 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  FileText, 
  Cpu, 
  Database, 
  Search,
  Sparkles,
  Link,
  ShieldAlert
} from 'lucide-react';

export default function App() {
  // Config
  const backendUrl = (import.meta.env.VITE_BACKEND_URL || 'http://localhost:7860').replace(/\/$/, '');
  
  // State
  const [file, setFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [extractedText, setExtractedText] = useState('');
  const [searchText, setSearchText] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  
  const [isAuditing, setIsAuditing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [streamingTokens, setStreamingTokens] = useState('');
  const [auditCards, setAuditCards] = useState([]);
  const [backendStatus, setBackendStatus] = useState('checking');

  const terminalEndRef = useRef(null);

  // Check backend health on mount
  useEffect(() => {
    fetch(backendUrl)
      .then(res => res.json())
      .then(() => setBackendStatus('connected'))
      .catch(() => setBackendStatus('disconnected'));
  }, [backendUrl]);

  // Scroll terminal to bottom when logs or tokens update
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, streamingTokens]);

  // Handle PDF upload
  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    if (!selectedFile.name.endsWith('.pdf')) {
      alert('Please upload a PDF file.');
      return;
    }

    setFile(selectedFile);
    setIsUploading(true);
    setExtractedText('');
    setAuditCards([]);
    setLogs([]);
    setStreamingTokens('');
    setFileId(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${backendUrl}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setFileId(data.file_id);
      setExtractedText(data.text);
      setLogs([`File "${selectedFile.name}" successfully parsed. Ready for audit.`]);
    } catch (err) {
      console.error(err);
      setLogs([`Error: Failed to process PDF file. Make sure backend is running.`]);
    } finally {
      setIsUploading(false);
    }
  };

  // Trigger Audit via SSE
  const startAudit = () => {
    if (!fileId) return;

    setIsAuditing(true);
    setLogs([`Starting adversarial financial audit...`]);
    setStreamingTokens('');
    setAuditCards([]);

    // SSE Endpoint Connection
    const eventSource = new EventSource(`${backendUrl}/api/agent/audit?file_id=${fileId}`);

    eventSource.addEventListener('log', (event) => {
      const logMsg = JSON.parse(event.data);
      setLogs((prev) => [...prev, logMsg]);
      setStreamingTokens(''); // Clear buffer on logs to divide steps
    });

    eventSource.addEventListener('token', (event) => {
      const token = event.data; // Raw token string
      setStreamingTokens((prev) => prev + token);
    });

    eventSource.addEventListener('card', (event) => {
      const cards = JSON.parse(event.data);
      setAuditCards(cards);
    });

    eventSource.addEventListener('error', (event) => {
      console.error('SSE Error:', event);
      setLogs((prev) => [...prev, `Pipeline Encountered Error.`]);
      setIsAuditing(false);
      eventSource.close();
    });

    eventSource.addEventListener('done', () => {
      setLogs((prev) => [...prev, `Forensic Audit Completed successfully.`]);
      setIsAuditing(false);
      eventSource.close();
    });
  };

  // Filtering extracted text in UI
  const getFilteredText = () => {
    if (!searchText) return extractedText;
    const lines = extractedText.split('\n');
    return lines
      .filter(line => line.toLowerCase().includes(searchText.toLowerCase()))
      .join('\n');
  };

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-card/60 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-tr from-accent-purple to-accent-indigo p-2.5 rounded-xl shadow-lg shadow-accent-purple/20">
            <ShieldAlert className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              AI PDF Earnings Call Auditor
            </h1>
            <p className="text-xs text-slate-400">Adversarial Forensic Contradiction Pipeline</p>
          </div>
        </div>

        {/* Telemetry/Env Stats */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800">
            <Cpu className="w-3.5 h-3.5 text-accent-purple" />
            <span className="text-slate-300">Model: Gemini-2.5 (OpenRouter)</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800">
            <Database className="w-3.5 h-3.5 text-accent-indigo" />
            <span className="text-slate-300">DB: Neon Postgres</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800">
            <div className={`w-2.5 h-2.5 rounded-full ${
              backendStatus === 'connected' ? 'bg-emerald-500 animate-pulse' : 
              backendStatus === 'disconnected' ? 'bg-red-500' : 'bg-amber-500'
            }`} />
            <span className="text-slate-300 capitalize">API Gateway: {backendStatus}</span>
          </div>
        </div>
      </header>

      {/* Main split-screen panel container */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Side: Document Panel */}
        <section className="w-1/2 border-r border-border flex flex-col p-6 overflow-hidden">
          <div className="mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2 text-slate-200">
              <FileText className="w-5 h-5 text-accent-indigo" />
              Earnings Call Transcript
            </h2>
            <p className="text-xs text-slate-400">Upload and preview the raw report context.</p>
          </div>

          {/* Upload Button area if no file ID */}
          {!fileId && (
            <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-800 rounded-2xl p-8 bg-card/20 hover:bg-card/40 hover:border-slate-700 transition duration-300">
              <div className="p-4 bg-slate-900 rounded-full border border-slate-800 mb-4">
                <UploadCloud className="w-10 h-10 text-slate-400" />
              </div>
              <p className="text-sm text-slate-300 mb-2 font-medium">Drag and drop your transcript PDF</p>
              <p className="text-xs text-slate-500 mb-6">PDF containing forecasts and historical tables</p>
              <label className="cursor-pointer bg-accent-indigo hover:bg-accent-indigo/90 text-white font-medium text-sm px-6 py-2.5 rounded-xl shadow-lg shadow-accent-indigo/20 transition">
                {isUploading ? 'Extracting Text...' : 'Select PDF File'}
                <input 
                  type="file" 
                  accept=".pdf" 
                  onChange={handleFileUpload} 
                  className="hidden" 
                  disabled={isUploading}
                />
              </label>
            </div>
          )}

          {/* File Parsed Text Display */}
          {fileId && (
            <div className="flex-1 flex flex-col overflow-hidden bg-card/30 border border-slate-800 rounded-2xl p-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-accent-indigo/20 text-accent-indigo px-2 py-0.5 rounded border border-accent-indigo/30 font-medium">PDF</span>
                  <span className="text-sm font-semibold truncate max-w-xs">{file?.name}</span>
                </div>
                <button 
                  onClick={() => { setFileId(null); setExtractedText(''); }} 
                  className="text-xs text-slate-500 hover:text-slate-300 transition"
                >
                  Clear File
                </button>
              </div>

              {/* Text Search Bar */}
              <div className="relative mb-3">
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                <input 
                  type="text" 
                  placeholder="Search and highlight financial terms..." 
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl py-2 pl-9 pr-4 text-sm focus:outline-none focus:border-accent-indigo transition"
                />
              </div>

              {/* Text content view */}
              <div className="flex-1 overflow-y-auto font-mono text-xs text-slate-400 p-3 bg-slate-950/80 border border-slate-900 rounded-xl whitespace-pre-wrap select-text leading-relaxed">
                {getFilteredText() || <span className="text-slate-600">No matching search text found.</span>}
              </div>
            </div>
          )}
        </section>

        {/* Right Side: Audit Terminal & Cards */}
        <section className="w-1/2 flex flex-col p-6 bg-slate-950/20 overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2 text-slate-200">
                <Terminal className="w-5 h-5 text-accent-purple" />
                Forensic Audit Console
              </h2>
              <p className="text-xs text-slate-400">Streamed LangGraph reasoning and contradictions.</p>
            </div>
            
            <button
              onClick={startAudit}
              disabled={!fileId || isAuditing}
              className={`flex items-center gap-2 font-medium text-sm px-6 py-2.5 rounded-xl shadow-lg transition duration-300 ${
                !fileId ? 'bg-slate-800 text-slate-500 cursor-not-allowed shadow-none' :
                isAuditing ? 'bg-slate-900 text-accent-purple border border-accent-purple/30 animate-pulse cursor-not-allowed shadow-none' :
                'bg-gradient-to-r from-accent-purple to-accent-indigo text-white hover:brightness-110 shadow-accent-purple/20'
              }`}
            >
              <Play className="w-4 h-4" />
              {isAuditing ? 'Auditing Run...' : 'Run Forensic Audit'}
            </button>
          </div>

          {/* Audit Logs Terminal */}
          <div className="h-64 bg-slate-950 border border-slate-800 rounded-2xl p-4 flex flex-col font-mono text-xs overflow-hidden mb-6 shadow-inner">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-900 mb-2 justify-between">
              <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">Agent Stream Logs</span>
              <div className="flex gap-1.5">
                <div className="w-2 h-2 rounded-full bg-red-500/60" />
                <div className="w-2 h-2 rounded-full bg-yellow-500/60" />
                <div className="w-2 h-2 rounded-full bg-green-500/60" />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2 select-text pr-2">
              {logs.map((log, index) => (
                <div key={index} className="text-emerald-400 flex gap-2">
                  <span className="text-slate-600 select-none">&gt;</span>
                  <span>{log}</span>
                </div>
              ))}
              {streamingTokens && (
                <div className="text-slate-300">
                  <span className="text-slate-600 select-none">&gt;</span>{' '}
                  <span className="bg-slate-900 px-1 py-0.5 rounded text-accent-purple border border-accent-purple/10 mr-1.5 font-bold">LLM Token stream:</span>
                  {streamingTokens}
                </div>
              )}
              {isAuditing && !streamingTokens && (
                <div className="text-slate-500 animate-pulse">Running graph node transitions...</div>
              )}
              {!isAuditing && logs.length === 0 && (
                <div className="text-slate-600 italic">Console idle. Upload a transcript PDF and click 'Run Forensic Audit' to begin.</div>
              )}
              <div ref={terminalEndRef} />
            </div>
          </div>

          {/* Generated Contradiction Cards */}
          <div className="flex-1 flex flex-col">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-accent-purple" />
              Identified Audit Cards ({auditCards.length})
            </h3>
            
            <div className="space-y-4">
              {auditCards.map((card, index) => {
                const isHigh = card.severity?.toLowerCase() === 'high';
                const isMed = card.severity?.toLowerCase() === 'med';
                const isLow = card.severity?.toLowerCase() === 'low';
                
                return (
                  <div 
                    key={index} 
                    className={`border rounded-2xl p-5 bg-card/40 backdrop-blur-sm shadow-md transition hover:-translate-y-0.5 duration-300 ${
                      isHigh ? 'border-red-500/30 hover:border-red-500/50' : 
                      isMed ? 'border-amber-500/30 hover:border-amber-500/50' : 
                      'border-emerald-500/30 hover:border-emerald-500/50'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="font-semibold text-base text-slate-200 pr-4">{card.title}</h4>
                      <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider border ${
                        isHigh ? 'bg-red-500/10 text-red-400 border-red-500/20' : 
                        isMed ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 
                        'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      }`}>
                        {card.severity} Severity
                      </span>
                    </div>

                    <p className="text-sm text-slate-300 mb-3 leading-relaxed">{card.description}</p>
                    
                    {card.contradiction_details && (
                      <div className="mt-3 pt-3 border-t border-slate-800/80">
                        <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1.5 font-medium">
                          <AlertTriangle className="w-3.5 h-3.5 text-accent-purple" />
                          Forensic Auditor Explanation
                        </div>
                        <p className="text-xs font-mono bg-slate-950/80 p-3 rounded-xl border border-slate-900 text-slate-400 leading-relaxed">
                          {card.contradiction_details}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}

              {!isAuditing && auditCards.length === 0 && (
                <div className="border border-slate-800/60 rounded-2xl p-8 text-center bg-card/10 italic text-slate-500 text-sm">
                  No Audit Cards generated yet. Run the auditor to view detected contradictions.
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
