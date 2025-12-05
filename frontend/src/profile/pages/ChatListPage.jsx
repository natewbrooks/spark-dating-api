import React from "react";

const MOCK_CHATS = [
  {
    id: 1,
    name: "Alex",
    age: 22,
    matchedAt: "2025-11-24",
    lastMessage: "Had fun talking last night 😊",
    avatarColor: "#f97316",
  },
  {
    id: 2,
    name: "Jordan",
    age: 21,
    matchedAt: "2025-11-23",
    lastMessage: "Let’s grab coffee sometime?",
    avatarColor: "#22c55e",
  },
];

export default function ChatListPage() {
  // Later: onClick should navigate to /chats/:id
  function handleOpenChat(chat) {
    console.log("Open chat", chat);
    alert(`Open chat with ${chat.name} (TODO)`);
  }

  return (
    <div className="h-full w-full px-4 py-3">
      <h1 className="text-2xl font-semibold mb-4">Your chats</h1>

      {MOCK_CHATS.length === 0 ? (
        <p className="text-sm text-neutral-400">
          You don’t have any saved chats yet. Join a Spark session to meet
          someone!
        </p>
      ) : (
        <ul className="space-y-3">
          {MOCK_CHATS.map((chat) => (
            <li key={chat.id}>
              <button
                onClick={() => handleOpenChat(chat)}
                className="w-full flex items-center gap-3 rounded-2xl border-t border-neutral-800 p-2 text-left transition"
              >
                {/* Avatar */}
                <div
                  className="h-11 w-11 rounded-full flex items-center justify-center text-base font-semibold"
                  style={{ backgroundColor: chat.avatarColor }}
                >
                  {chat.name[0]}
                </div>

                {/* Text content */}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold text-white">
                      {chat.name}, {chat.age}
                    </p>
                    <p className="text-xs text-neutral-400">
                      Matched {chat.matchedAt}
                    </p>
                  </div>
                  <p className="text-sm text-neutral-400 truncate">
                    {chat.lastMessage}
                  </p>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
