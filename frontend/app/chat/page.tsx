"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "model";
  content: string;
}

interface ChatObj {
  id: number;
}

export default function ChatPage() {
  const router = useRouter();

  const [token, setToken] = useState<string | null>(null);
  const [chats, setChats] = useState<ChatObj[]>([]);
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    if (!savedToken) {
      router.push("/login");
    } else {
      setToken(savedToken);
      fetchChats(savedToken);
    }
  }, [router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchChats = async (jwt: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chats`, {
        headers: { Authorization: `Bearer ${jwt}` },
      });
      if (res.ok) {
        const data = await res.json();
        setChats(data.reverse()); // Plus récents en haut
      } else if (res.status === 401) {
        localStorage.removeItem("token");
        router.push("/login");
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadChat = async (chatId: number) => {
    if (!token) return;
    setActiveChatId(chatId);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chats/${chatId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const createChat = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chats`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setChats((prev) => [data, ...prev]);
        setActiveChatId(data.id);
        setMessages([]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    // Si aucun chat actif, on en crée un automatiquement
    let currentChatId = activeChatId;
    if (!currentChatId && input.trim()) {
      try {
        const createRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chats`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (createRes.ok) {
          const data = await createRes.json();
          currentChatId = data.id;
          setChats((prev) => [data, ...prev]);
          setActiveChatId(currentChatId!);
        }
      } catch (err) { console.error(err); }
    }

    if (!input.trim() || !currentChatId || !token) return;

    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setIsLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chats/${currentChatId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content: userMsg }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [...prev, { role: "model", content: data.response }]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="w-10 h-10 border-4 border-t-purple-600 border-gray-200 rounded-full animate-spin"></div>
    </div>
  );

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 font-sans overflow-hidden">
      {/* SIDEBAR (GAUCHE) */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col z-10 shrink-0">
        <div className="h-20 flex items-center justify-center border-b border-gray-100 cursor-pointer" onClick={() => router.push("/")}>
          <Image src="/images/NEWSFOUNDRY.svg" alt="NewsFoundry" width={140} height={25} className="brightness-0" style={{ filter: 'invert(33%) sepia(87%) saturate(1476%) hue-rotate(242deg) brightness(85%) contrast(100%)' }} />
        </div>

        <div className="flex-1 overflow-y-auto">
          {chats.map((chat) => (
            <div
              key={chat.id}
              onClick={() => loadChat(chat.id)}
              className={`w-full text-left px-5 py-4 border-b border-gray-100 cursor-pointer transition-colors ${activeChatId === chat.id ? "bg-purple-50" : "hover:bg-gray-50"}`}
            >
              <h3 className="text-sm font-medium text-gray-800">Discussion #{chat.id}</h3>
              <p className="text-xs text-gray-400 mt-1">Cliquez pour reprendre</p>
            </div>
          ))}
          {chats.length === 0 && (
            <p className="text-gray-500 text-sm px-4 text-center mt-10 italic">Aucune historique.</p>
          )}
        </div>

        <div className="p-4 border-t border-gray-100">
          <button onClick={() => { localStorage.removeItem("token"); router.push("/"); }} className="w-full text-left px-3 py-2 text-gray-600 hover:text-red-600 text-sm rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
            Se déconnecter
          </button>
        </div>
      </div>

      {/* ZONE CENTRALE (DROITE) */}
      <div className="flex-1 flex flex-col bg-[#EBEAF2] relative">

        {/* TABS TOP BAR */}
        <div className="h-20 border-b border-gray-200/50 bg-[#EBEAF2] flex items-center px-6 gap-3 pt-2">
          <button onClick={createChat} className="bg-[#7B3FE4] text-white px-5 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 shadow-sm">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
            Chat
          </button>
          <button className="bg-gray-100 text-gray-600 hover:bg-gray-200 px-5 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" /></svg>
            Revue de presse
          </button>
        </div>

        {/* MESSAGES AREA */}
        <div className="flex-1 overflow-y-auto w-full max-w-5xl mx-auto p-6 md:p-10 space-y-8 flex flex-col">
          {(!activeChatId || messages.length === 0) ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="flex flex-col items-center bg-white rounded-2xl shadow-sm p-10 md:p-14 w-full max-w-2xl text-center">
                <Image src="/images/union-3.svg" alt="NewsFoundry" width={81} height={76} color="#803CDA" className="mb-10" />
                <h2 className="text-3xl font-medium text-[#7B3FE4] mb-6">Assistant Revue de Presse IA</h2>
                <p className="text-gray-500 mb-10 text-base leading-relaxed">
                  Posez-moi des questions sur l'actualité récente ou demandez-moi de générer une revue de presse sur un sujet spécifique.
                </p>

                <div className="text-sm text-gray-700 space-y-4 text-left inline-block">
                  <p className="font-bold text-center mb-2 text-gray-500 uppercase tracking-wider text-xs">Exemples :</p>
                  <p className="flex items-center gap-2"><span className="w-1.5 h-1.5 bg-gray-400 border border-gray-300 rounded-full"></span> "Quelles sont les dernières nouvelles en politique ?"</p>
                  <p className="flex items-center gap-2"><span className="w-1.5 h-1.5 bg-gray-400 border border-gray-300 rounded-full"></span> "Génère une revue de presse sur la technologie"</p>
                  <p className="flex items-center gap-2"><span className="w-1.5 h-1.5 bg-gray-400 border border-gray-300 rounded-full"></span> "Résume l'actualité économique de la semaine"</p>
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] md:max-w-[75%] p-5 rounded-2xl shadow-sm ${msg.role === "user" ? "bg-[#7B3FE4] text-white rounded-br-sm" : "bg-white text-gray-800 rounded-bl-sm"}`}>
                    {msg.role === "model" ? (
                      <div className="prose prose-p:leading-relaxed prose-pre:bg-gray-50 prose-pre:border prose-pre:border-gray-200 prose-pre:rounded-xl max-w-none text-sm md:text-base break-words">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap text-sm md:text-base leading-relaxed font-medium">{msg.content}</p>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white p-5 rounded-2xl rounded-bl-sm shadow-sm flex items-center gap-3">
                    <div className="w-2.5 h-2.5 bg-[#7B3FE4]/40 rounded-full animate-bounce"></div>
                    <div className="w-2.5 h-2.5 bg-[#7B3FE4]/70 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                    <div className="w-2.5 h-2.5 bg-[#7B3FE4] rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} className="pb-4" />
            </>
          )}
        </div>

        {/* INPUT BAR (BOTTOM) */}
        <div className="bg-white p-4 shrink-0">
          <form onSubmit={sendMessage} className="max-w-4xl mx-auto relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Tapez votre message ici..."
              disabled={isLoading}
              className="w-full bg-[#f4f4f5] border-none text-gray-800 rounded-xl pl-5 pr-16 py-4 focus:outline-none focus:ring-2 focus:ring-[#7B3FE4] transition-all disabled:opacity-50 placeholder:text-gray-400"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className={`absolute right-3 p-2.5 rounded-lg transition-all flex items-center justify-center ${input.trim() && !isLoading ? 'bg-[#7B3FE4] text-white hover:bg-purple-700' : 'bg-gray-300 text-gray-100 cursor-not-allowed'}`}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
