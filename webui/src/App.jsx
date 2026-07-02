import React, { useState, useEffect, useRef } from 'react';
import { Send } from 'lucide-react';
import Sidebar from './components/Sidebar'

const MessageContent = ({ content }) => {
  const URL_PATTERN = /\b(?:https?:\/\/|www\.)[^\s<]+\b/g;
  const parts = [];
  let lastIndex = 0;
  const matches = [...content.matchAll(URL_PATTERN)];

  matches.forEach((match) => {
    const url = match[0];
    const startIndex = match.index;

    if (startIndex > lastIndex) {
      parts.push(content.slice(lastIndex, startIndex));
    }

    let href = url.startsWith('www.') ? `https://${url}` : url;
    try {
      const urlObj = new URL(href);
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        parts.push(url);
        lastIndex = startIndex + url.length;
        return;
      }
    } catch {
      parts.push(url);
      lastIndex = startIndex + url.length;
      return;
    }

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

  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }
  return <>{parts}</>;
};

function App() {
  const [peers, setPeers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selectedPeerIp, setSelectedPeerIp] = useState(null); // Tracks by IP:PORT
  const [text, setText] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, selectedPeerIp]);

  // Robustly fetch peers with exact IPs from the REST API
  const fetchPeers = async () => {
    try {
      const res = await fetch('/api/peers');
      const data = await res.json();
      setPeers(data);
      
      // Auto-deselect if the peer dropped offline
      setSelectedPeerIp(current => {
        if (current && !data.find(p => p.ip === current)) return null;
        return current;
      });
    } catch (e) {
      console.error("Failed to fetch peers:", e);
    }
  };

  useEffect(() => {
    fetchPeers(); // Initial load

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/api/ws`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'PEER_LIST_UPDATE') {
        // Trigger a fresh fetch so we have exact IP:PORT strings for routing
        fetchPeers(); 
      }
      
      if (data.type === 'NEW_MESSAGE') {
        setMessages(prev => [...prev, {
          sender: data.payload.sender, // Backend sends IP:PORT here
          recipient: 'you',
          content: data.payload.content,
          timestamp: new Date()
        }]);
      }
    };

    return () => ws.close();
  }, []);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!selectedPeerIp || !text.trim()) return;

    const message = { 
      sender: 'you', 
      recipient: selectedPeerIp, 
      content: text, 
      timestamp: new Date() 
    };
    
    setMessages(prev => [...prev, message]);
    
    fetch('/api/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient_ip: selectedPeerIp, content: text }),
    });
    
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  // Filter messages so we only see the chat history for the selected user!
  const currentMessages = messages.filter(m => 
    (m.sender === selectedPeerIp && m.recipient === 'you') || 
    (m.sender === 'you' && m.recipient === selectedPeerIp)
  );

  const getSelectedPeerName = () => {
    if (!selectedPeerIp) return '';
    const p = peers.find(x => x.ip === selectedPeerIp);
    return p ? p.nickname : selectedPeerIp;
  };

  return (
    <div className="flex h-screen bg-black text-green-400 font-mono overflow-hidden" style={{ fontFamily: '"Courier New", monospace' }}>
      <div className={`${selectedPeerIp ? 'hidden' : 'flex'} md:flex w-full md:w-64 flex-shrink-0 h-full`}>
        <Sidebar 
          peers={peers} 
          selectedPeerIp={selectedPeerIp} 
          setSelectedPeerIp={setSelectedPeerIp} 
        />
      </div>

      <main className={`${selectedPeerIp ? 'flex' : 'hidden'} md:flex flex-1 flex flex-col bg-black border-2 border-green-400 m-2`}>
        <div className="bg-green-400 text-black px-4 py-2 font-bold text-sm flex justify-between items-center">
          <div className="flex items-center gap-2">
            {selectedPeerIp && (
              <button 
                onClick={() => setSelectedPeerIp(null)} 
                className="md:hidden mr-2 border border-black px-2 py-0.5 rounded text-xs font-bold hover:bg-black hover:text-green-400 transition-colors"
              >
                &lt; BACK
              </button>
            )}
            <div>
              {selectedPeerIp ? `[CONNECTED] ${getSelectedPeerName()}` : '[STANDBY] Select a peer'}
            </div>
          </div>
          <div className="text-xs opacity-70">
            {new Date().toLocaleTimeString()}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {!selectedPeerIp ? (
            <div className="text-green-700 text-sm italic">
              <div>$ awaiting_peer_selection...</div>
              <div className="mt-4">Select a peer from the list to begin transmission.</div>
            </div>
          ) : currentMessages.length === 0 ? (
            <div className="text-green-700 text-sm italic">
              <div>$ secure_channel_established_with: {getSelectedPeerName()}</div>
              <div className="mt-2">Waiting for messages...</div>
            </div>
          ) : (
            currentMessages.map((m, i) => (
              <div key={i} className="text-sm space-y-1">
                <div className="text-green-300">
                  [{m.timestamp.toLocaleTimeString()}] {m.sender === 'you' ? '< OUT' : '> IN'}
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
              placeholder={selectedPeerIp ? `Message ${getSelectedPeerName()}...` : 'Select peer first...'}
              disabled={!selectedPeerIp}
              className="flex-1 bg-black border-0 outline-none text-green-400 placeholder-green-700 caret-green-400 resize-none overflow-y-auto leading-10"
              style={{ minHeight: '40px', maxHeight: '120px' }}
              rows={1}
              autoFocus
            />
            <button
              onClick={handleSendMessage}
              disabled={!selectedPeerIp || !text.trim()}
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