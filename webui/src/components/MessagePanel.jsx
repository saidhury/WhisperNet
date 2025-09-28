import React from 'react';

export default function MessagePanel({ selectedPeer, messages, onSendMessage }) {
    const [text, setText] = React.useState('');
    const handleSubmit = (e) => {
        e.preventDefault();
        if (!text.trim()) return;
        onSendMessage(text);
        setText('');
    };
    return (
        <div className="w-3/4 flex flex-col">
            <div className="flex-grow p-4">
                {selectedPeer ? `Chatting with ${selectedPeer}` : 'Select a peer to chat'}
                <ul>{messages.map((m, i) => <li key={i}>{m.sender}: {m.content}</li>)}</ul>
            </div>
            <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700">
                <input
                    type="text"
                    value={text}
                    onChange={e => setText(e.target.value)}
                    placeholder="Message..."
                    className="w-full p-2 rounded bg-gray-700 border border-gray-600"
                    disabled={!selectedPeer}
                />
            </form>
        </div>
    );
}
