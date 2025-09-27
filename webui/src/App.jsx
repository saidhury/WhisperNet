import React, { useState, useEffect } from 'react';

function App() {
  const [peers, setPeers] = useState([]);
  const [selectedPeer, setSelectedPeer] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/api/ws`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'PEER_LIST_UPDATE') {
        setPeers(data.payload);
      }
    };
    return () => ws.close();
  }, []);

  return (
    <div className="flex h-screen">
      <div className="w-1/4 bg-gray-800 text-white p-4">
        <h2 className="text-xl font-bold">Peers</h2>
        <ul>
          {peers.map(peer => (
            <li key={peer} onClick={() => setSelectedPeer(peer)} className="cursor-pointer">
              {peer}
            </li>
          ))}
        </ul>
      </div>
      <div className="w-3/4 flex flex-col">
        <div className="flex-grow p-4">
          {selectedPeer ? `Chatting with ${selectedPeer}` : 'Select a peer to chat'}
        </div>
      </div>
    </div>
  );
}

export default App;
