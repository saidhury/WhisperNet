import React, { useState, useEffect } from 'react';
import MessagePanel from './components/MessagePanel.jsx';

function App() {
  const [peers, setPeers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selectedPeer, setSelectedPeer] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/api/ws`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'PEER_LIST_UPDATE') {
        setPeers(data.payload);
      }
      if (data.type === 'NEW_MESSAGE') {
        setMessages(prev => [...prev, data.payload]);
      }
    };
    return () => ws.close();
  }, []);
  
  const handleSendMessage = (text) => {
    const message = { sender: 'you', content: text };
    setMessages(prev => [...prev, message]);
    fetch('/api/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient_ip: selectedPeer, content: text }),
    });
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <div className="w-1/4 bg-gray-800 p-4">
        <h2 className="text-xl font-bold">Peers</h2>
        <ul>
          {peers.map(peer => (
            <li key={peer} onClick={() => setSelectedPeer(peer)} className="cursor-pointer p-2 hover:bg-gray-700">
              {peer}
            </li>
          ))}
        </ul>
      </div>
      <MessagePanel selectedPeer={selectedPeer} messages={messages} onSendMessage={handleSendMessage} />
    </div>
  );
}
export default App;
