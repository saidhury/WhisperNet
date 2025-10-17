import React, { useState, useEffect, useRef } from 'react';
import { Send } from 'lucide-react';
import Sidebar from './components/Sidebar'

// Component to render message content with clickable links
const MessageContent = ({ content }) => {
  // URL regex pattern that matches http://, https://, and www. URLs
  const URL_PATTERN = /\b(?:https?:\/\/|www\.)[^\s<]+\b/g;
  const parts = [];
  let lastIndex = 0;

  // Use matchAll to safely iterate URLs
  const matches = [...content.matchAll(URL_PATTERN)];

  matches.forEach((match) => {
    const url = match[0];
    const startIndex = match.index;

    // Add plain text before the link
    if (startIndex > lastIndex) {
      parts.push(content.slice(lastIndex, startIndex));
    }

    // Normalize link (add https:// for www.)
    let href = url.startsWith('www.') ? `https://${url}` : url;

    // ✅ Validate URL scheme for security
    try {
      const urlObj = new URL(href);
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        // Skip invalid or non-http(s) URLs
        parts.push(url);
        lastIndex = startIndex + url.length;
        return;
      }
    } catch {
      // If invalid URL, render as plain text
      parts.push(url);
      lastIndex = startIndex + url.length;
      return;
    }

    // Add clickable link
    parts.push(
      <a
        key={startIndex}
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-500 underline hover:text-blue-700"
      >
        {url}
      </a>
    );

    lastIndex = startIndex + url.length;
  });

  // Add remaining text after last link
  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return <>{parts}</>;
};

function App() {
  // peers will be array of { ip, nickname }
  const [peers, setPeers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selectedPeer, setSelectedPeer] = useState(null);
  const [text, setText] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/api/ws`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'PEER_LIST_UPDATE') {
        const newPeers = data.payload;
        setPeers(newPeers);
        // If the selected peer is no longer in the list, deselect them.
        setSelectedPeer(currentSelectedPeer => {
          if (currentSelectedPeer && !newPeers.includes(currentSelectedPeer)) {
            return null;
          }
          return currentSelectedPeer;
        });
      }
      if (data.type === 'NEW_MESSAGE') {
        setMessages(prev => [...prev, data.payload]);
      }
    };

    ws.onopen = () => console.log("WebSocket connected");
    ws.onclose = () => console.log("WebSocket disconnected");
    ws.onerror = (error) => console.error("WebSocket error:", error);

    return () => {
      ws.close();
    };
  }, []);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!selectedPeer || !text.trim()) return;
    
    const message = { sender: 'you', content: text };
    setMessages(prev => [...prev, message]);
    
    fetch('/api/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient_ip: selectedPeer, content: text }),
    });
    
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  return (
    <div className="flex h-screen bg-black text-green-400 font-mono overflow-hidden" style={{ fontFamily: '"Courier New", monospace' }}>
      <Sidebar peers={peers} selectedPeer={selectedPeer} setSelectedPeer={setSelectedPeer} />

      <main className="flex-1 flex flex-col bg-black border-2 border-green-400 m-2">
          <div className="bg-green-400 text-black px-4 py-2 font-bold text-sm flex justify-between items-center">
          <div>
            {selectedPeer ? (`[CONNECTED] ${(() => {
              const p = peers.find(x => x.ip === selectedPeer);
              return p ? (p.nickname || p.ip) : selectedPeer;
            })()}`) : '[STANDBY] Select a peer'}
          </div>
          <div className="text-xs opacity-70">
            {new Date().toLocaleTimeString()}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {!selectedPeer ? (
            <div className="text-green-700 text-sm italic">
              <div>$ awaiting_peer_selection...</div>
              <div className="mt-4">Select a peer from the list to begin transmission.</div>
            </div>
          ) : messages.length === 0 ? (
            <div className="text-green-700 text-sm italic">
              <div>$ connection_established</div>
              <div className="mt-2">Waiting for messages...</div>
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className="text-sm space-y-1">
                <div className="text-green-300">
                  [{new Date().toLocaleTimeString()}] {m.sender === 'you' ? '< OUT' : '> IN'}
                </div>
                <div className={`pl-4 border-l-2 ${m.sender === 'you' ? 'border-green-600' : 'border-green-400'}`}>
                  <span className="text-green-400">
                    <MessageContent content={m.content} />
                  </span>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t-2 border-green-400 bg-black p-4">
          <div className="flex gap-2">
            <span className="text-green-400 leading-10">$</span>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={selectedPeer ? 'Enter message... (Shift+Enter for new line)' : 'Select peer first...'}
              disabled={!selectedPeer}
              className="flex-1 bg-black border-0 outline-none text-green-400 placeholder-green-700 caret-green-400 resize-none overflow-y-auto leading-10"
              style={{ minHeight: '40px', maxHeight: '120px' }}
              rows={1}
              autoFocus
            />
            <button
              onClick={handleSendMessage}
              disabled={!selectedPeer || !text.trim()}
              className="text-green-400 hover:text-green-300 disabled:text-green-700 transition-colors self-start leading-10"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;