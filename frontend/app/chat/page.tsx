"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "model";
  content: string;
}

interface ArticleSummary {
  title: string;
  summary: string;
}

interface PressRelease {
  title: string;
  general_summary: string;
  articles: ArticleSummary[];
  created_at?: string;
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

  // États pour la revue de presse
  const [pressReleases, setPressReleases] = useState<PressRelease[]>([]);
  const [isPressModalOpen, setIsPressModalOpen] = useState(false);
  const [pressTopic, setPressTopic] = useState("");
  const [isGeneratingPress, setIsGeneratingPress] = useState(false);
  const [mode, setMode] = useState("chat");


  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
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
        // Le backend renvoie { "messages": [...], "press_releases": [...] }
        if (data && data.messages) {
          setMessages(data.messages);
          setPressReleases(data.press_releases || []);
        } else if (Array.isArray(data)) {
          setMessages(data);
        }
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

  const generatePressRelease = async () => {
    if (!token || !activeChatId || !pressTopic.trim()) return;
    setIsGeneratingPress(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chats/${activeChatId}/press-release`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ topic: pressTopic }),
      });

      if (res.ok) {
        setIsPressModalOpen(false);
        setPressTopic("");
        router.push("/revue"); // Redirection vers la page des revues après succès
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsGeneratingPress(false);
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
    <div className="flex h-screen bg-[#F0F2F5] text-gray-900 font-sans overflow-hidden">

      {/* MODALE GÉNÉRATION REVUE DE PRESSE */}
      {isPressModalOpen && (
        <div className="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="p-6 md:p-8 flex flex-col gap-6">
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <h3 className="text-xl font-bold text-gray-900">Générer une revue de presse</h3>
                  <p className="text-sm text-gray-500">Donner un titre à votre revue de presse</p>
                </div>
                <button
                  onClick={() => setIsPressModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600 text-xs font-medium"
                >
                  Fermer
                </button>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700">Thème de la revue de presse</label>
                <input
                  type="text"
                  value={pressTopic}
                  onChange={(e) => setPressTopic(e.target.value)}
                  placeholder="Tapez le thème..."
                  className="w-full bg-[#f4f4f5] border border-transparent rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-purple-400 transition-all"
                  autoFocus
                />
              </div>

              <button
                onClick={generatePressRelease}
                disabled={!pressTopic.trim() || isGeneratingPress}
                className="w-full bg-[#2D2D35] text-white py-3 rounded-lg font-bold text-sm hover:bg-black transition-all disabled:opacity-50"
              >
                {isGeneratingPress ? "Génération en cours..." : "Générer"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SIDEBAR */}
      <div className={`fixed inset-y-0 left-0 transform ${isSidebarOpen ? "translate-x-0" : "-translate-x-full"} md:relative md:translate-x-0 transition-transform duration-300 ease-in-out w-64 bg-[#F9F9FB] border-r border-gray-100 flex flex-col z-50 shrink-0`}>
        <div className="h-20 flex items-center px-6 border-b border-gray-50">
          <Image
            src="/images/NEWSFOUNDRY.svg"
            alt="NewsFoundry"
            width={130}
            height={24}
            style={{ filter: 'invert(33%) sepia(87%) saturate(1476%) hue-rotate(242deg) brightness(85%) contrast(100%)' }}
          />
          <Image src="/images/Union-3.svg" alt="Bot" width={80} height={80} className="w-4 h-4" />
        </div>

        <div className="flex-1 overflow-y-auto">
          {chats.map((chat) => (
            <div
              key={chat.id}
              onClick={() => loadChat(chat.id)}
              className={`w-full text-left px-6 py-4 border-b border-gray-50 cursor-pointer transition-colors ${activeChatId === chat.id ? "bg-white shadow-[inset_4px_0_0_0_rgba(123,63,228,0.2)]" : "hover:bg-gray-50"}`}
            >
              <h3 className={`text-sm ${activeChatId === chat.id ? "font-bold text-gray-800" : "font-medium text-gray-500"}`}>Discussion du</h3>
              <p className="text-[11px] text-gray-400 font-normal">10/12/2026</p>
            </div>
          ))}
        </div>

        <div className="p-6 border-t border-gray-100">
          <button onClick={() => { localStorage.removeItem("token"); router.push("/"); }} className="flex items-center gap-2.5 text-gray-500 hover:text-red-500 text-sm font-medium transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
            Se déconnecter
          </button>
        </div>
      </div>

      {/* ZONE CENTRALE */}
      <div className="flex-1 flex flex-col bg-[#E8E9F1]">

        {/* TOP BAR */}
        <div className="h-20 bg-white border-b border-gray-100 flex items-center px-6">
          {!activeChatId ? (
            /* ÉTAT ONGLET (Image 1 & 2) */
            <div className="flex bg-[#F3F4F6] p-1 rounded-xl">
              <button
                onClick={() => setMode("chat")}
                className={`flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-bold transition-all ${mode === "chat" ? "bg-[#7B3FE4] text-white shadow-md" : "text-gray-500 hover:text-gray-700"}`}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Chat
              </button>
              <button
                onClick={() => router.push("/revue")}
                className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-bold text-gray-500 hover:text-gray-700"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Revue de presse
              </button>
            </div>
          ) : (
            /* ÉTAT DISCUSSION ACTIVE (Image 3) */
            <div className="flex items-center w-full gap-4">
              <button
                onClick={() => setActiveChatId(null)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>

              <div className="flex flex-col flex-1">
                <h2 className="text-[17px] font-bold text-gray-900 leading-tight">Nouvelle discussion</h2>
                <p className="text-[13px] text-gray-400 font-medium">Conversation active</p>
              </div>

              <button
                onClick={() => setIsPressModalOpen(true)}
                className="bg-[#7B3FE4] text-white px-6 py-3 rounded-xl text-sm font-bold hover:bg-purple-700 transition-all flex items-center gap-3 shadow-sm"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Générer une revue de presse
              </button>
            </div>
          )}
        </div>

        {/* MESSAGES AREA */}
        <div className="flex-1 overflow-y-auto px-6 py-8 space-y-10 flex flex-col items-center">
          {(!activeChatId || messages.length === 0) ? (
            <div className="flex-1 flex items-center justify-center w-full">
              <div className="bg-white rounded-[2rem] shadow-sm p-14 w-full max-w-2xl text-center flex flex-col items-center gap-8">
                <Image src="/images/Union-3.svg" alt="Bot" width={80} height={80} className="w-20 h-20" />
                <h2 className="text-4xl font-normal text-[#7B3FE4] tracking-tight">Assistant Revue de Presse IA</h2>

                <div className="space-y-6">
                  <p className="text-gray-400 text-lg">
                    Posez-moi des questions sur l'actualité récente ou demandez-moi de générer une revue de presse sur un sujet spécifique.
                  </p>

                  <div className="space-y-3 pt-4">
                    <p className="text-[12px] font-bold text-gray-500 uppercase tracking-widest">Exemples :</p>
                    <ul className="text-[14px] text-gray-400 space-y-1 list-none">
                      <li>"Quelles sont les dernières nouvelles en politique ?"</li>
                      <li>"Génère une revue de presse sur la technologie"</li>
                      <li>"Résumé l'actualité économique de la semaine"</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="w-full max-w-5xl space-y-10 pb-10">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex items-start gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  {msg.role === "model" && (
                    <div className="w-8 h-8 rounded-full bg-white border border-gray-100 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                      <Image src="/images/Union-3.svg" alt="Bot" width={80} height={80} className="w-4 h-4 brightness-0" />
                    </div>
                  )}

                  <div className="flex flex-col gap-1.5 max-w-[70%]">
                    <div className={`p-5 rounded-[1.25rem] ${msg.role === "user" ? "bg-[#2D2D35] text-white rounded-tr-sm" : "bg-[#F3F4F6] text-gray-800 rounded-tl-sm"}`}>
                      {msg.role === "model" ? (
                        <div className="prose prose-sm max-w-none text-[14.5px] leading-relaxed prose-p:my-1">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="text-[14.5px] leading-relaxed">{msg.content}</p>
                      )}
                    </div>
                    <span className="text-[11px] text-gray-400 font-medium px-2">10:31</span>
                  </div>

                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-black flex items-center justify-center shrink-0 mt-1 overflow-hidden">
                      <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" /></svg>
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-white border border-gray-100 flex items-center justify-center animate-pulse shadow-sm">
                    <Image src="/images/Union-3.svg" alt="Thinking" width={80} height={80} className="w-4 h-4 brightness-0 opacity-50" />
                  </div>
                  <div className="bg-[#F3F4F6] px-5 py-3 rounded-2xl rounded-tl-sm text-gray-400 text-xs italic">L'IA réfléchit...</div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* INPUT BAR */}
        <div className="p-6 bg-white shrink-0">
          <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex items-center gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Tapez votre message ici..."
                disabled={isLoading}
                className="w-full bg-[#f4f4f5] border border-gray-100 text-gray-800 rounded-xl pl-6 py-4 text-[15px] focus:outline-none focus:ring-1 focus:ring-purple-400 focus:bg-white transition-all placeholder:text-gray-400"
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className={`p-3.5 rounded-xl transition-all ${input.trim() && !isLoading ? 'bg-[#7B3FE4] text-white hover:bg-purple-700' : 'bg-[#D1D5DB] text-white'}`}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
