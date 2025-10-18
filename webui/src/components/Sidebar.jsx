import React from 'react';
import PropTypes from 'prop-types';
import { Terminal, Zap } from 'lucide-react';

const APP_VERSION = import.meta.env.VITE_APP_VERSION || 'v0.1.0';

const Sidebar = ({ peers = [], selectedPeer = null, setSelectedPeer }) => {
  const handleKeyDown = (e, peer, index) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setSelectedPeer(peer);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = (index + 1) % peers.length;
      setSelectedPeer(peers[nextIndex]);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = index === 0 ? peers.length - 1 : index - 1;
      setSelectedPeer(peers[prevIndex]);
    } else if (e.key === 'Home') {
      e.preventDefault();
      if (peers.length) setSelectedPeer(peers[0]);
    } else if (e.key === 'End') {
      e.preventDefault();
      if (peers.length) setSelectedPeer(peers[peers.length - 1]);
    }
  };

  // Ensure roving tabindex always exposes at least one tabbable option
  const hasValidSelection = selectedPeer != null && peers.includes(selectedPeer);
  return (
    <aside className="w-64 bg-black border-r-2 border-green-400 flex flex-col overflow-hidden">
      <div className="p-4 border-b-2 border-green-400">
        <div className="flex items-center gap-2 mb-2">
          <Terminal size={20} aria-hidden="true" />
          <h1 className="text-lg font-bold tracking-wider">WHISPERNET</h1>
        </div>
        <div className="text-xs text-green-300 opacity-70">{APP_VERSION}</div>
      </div>

      <div className="p-4 border-b border-green-400 opacity-70">
        <div className="text-xs uppercase tracking-widest mb-2">Status</div>
        <div className="flex items-center gap-2" aria-live="polite" aria-atomic="true">
          <Zap size={14} className="text-green-300" aria-hidden="true" />
          <span className="text-sm">
            {peers.length > 0 ? `${peers.length} peer${peers.length !== 1 ? 's' : ''} online` : 'Scanning...'}
          </span>
        </div>
      </div>

      <div className="flex-1 flex flex-col p-4">
        <div className="text-xs uppercase tracking-widest mb-3 text-green-300">Connected Peers</div>
        <ul
          className="space-y-1 overflow-y-auto flex-1"
          role="listbox"
          aria-label="Connected Peers"
          aria-busy={peers.length === 0}
        >
          {peers.length > 0 ? (
            peers.map((peer, index) => (
              <li
                key={peer}
                tabIndex={hasValidSelection ? (selectedPeer === peer ? 0 : -1) : (index === 0 ? 0 : -1)}
                role="option"
                aria-selected={selectedPeer === peer}
                onClick={() => setSelectedPeer(peer)}
                onKeyDown={(e) => handleKeyDown(e, peer, index)}
                className={`p-2 rounded cursor-pointer text-sm transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-green-400 ${
                  selectedPeer === peer
                    ? 'bg-green-400 text-black font-bold'
                    : 'hover:bg-green-900 hover:text-green-300 border border-green-700'
                }`}
              >
                <span className="text-xs opacity-60">→ </span>{peer}
              </li>
            ))
          ) : (
            <li role="none" className="text-green-700 text-sm italic">No peers detected</li>
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

Sidebar.propTypes = {
  peers: PropTypes.arrayOf(PropTypes.string).isRequired,
  selectedPeer: PropTypes.string,
  setSelectedPeer: PropTypes.func.isRequired,
};

export default Sidebar;
