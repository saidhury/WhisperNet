import React from 'react';
import { Terminal, Zap } from 'lucide-react';

const Sidebar = ({ peers, selectedPeer, setSelectedPeer }) => {
  return (
    <aside className="w-64 bg-black border-r-2 border-green-400 flex flex-col overflow-hidden">
      <div className="p-4 border-b-2 border-green-400">
        <div className="flex items-center gap-2 mb-2">
          <Terminal size={20} />
          <h1 className="text-lg font-bold tracking-wider">WHISPERNET</h1>
        </div>
        <div className="text-xs text-green-300 opacity-70">v0.1.0</div>
      </div>

      <div className="p-4 border-b border-green-400 opacity-70">
        <div className="text-xs uppercase tracking-widest mb-2">Status</div>
        <div className="flex items-center gap-2">
          <Zap size={14} className="text-green-300" />
          <span className="text-sm">
            {peers.length > 0 ? `${peers.length} peer${peers.length !== 1 ? 's' : ''} online` : 'Scanning...'}
          </span>
        </div>
      </div>

      <div className="flex-1 flex flex-col p-4">
        <div className="text-xs uppercase tracking-widest mb-3 text-green-300">Connected Peers</div>
        <ul className="space-y-1 overflow-y-auto flex-1">
          {peers.length > 0 ? (
            peers.map(peer => (
              <li
                key={peer}
                onClick={() => setSelectedPeer(peer)}
                className={`p-2 rounded cursor-pointer text-sm transition-all ${
                  selectedPeer === peer
                    ? 'bg-green-400 text-black font-bold'
                    : 'hover:bg-green-900 hover:text-green-300 border border-green-700'
                }`}
              >
                <span className="text-xs opacity-60">→ </span>{peer}
              </li>
            ))
          ) : (
            <li className="text-green-700 text-sm italic">No peers detected</li>
          )}
        </ul>
      </div>

      <div className="p-4 border-t border-green-400 text-xs opacity-50">
        <div>whispernet@node</div>
        <div>session_active</div>
      </div>
    </aside>
  );
};

export default Sidebar;
