"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import ReactMarkdown from "react-markdown";

interface ArticleSummary {
  title: string;
  summary: string;
}

interface PressRelease {
  title: string;
  general_summary: string;
  articles: ArticleSummary[];
  chat_id: number;
  created_at?: string;
}

export default function PressReleasesPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [releases, setReleases] = useState<PressRelease[]>([]);
  const [chats, setChats] = useState<any[]>([]);
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const showError = (msg: string) => {
    setError(msg);
    setTimeout(() => setError(null), 5000);
  };

  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    if (!savedToken) {
      router.push("/login");
    } else {
      setToken(savedToken);
      fetchAllReleases(savedToken);
      fetchChats(savedToken);
    }
  }, [router]);

  const fetchChats = async (jwt: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chats`, {
        headers: { Authorization: `Bearer ${jwt}` },
      });
      if (res.ok) {
        const data = await res.json();
        setChats(data.reverse());
      } else if (res.status === 401) {
        localStorage.removeItem("token");
        router.push("/login");
      } else {
        showError("Erreur lors du chargement des discussions.");
      }
    } catch (err) {
      console.error(err);
      showError("Impossible de se connecter au serveur.");
    }
  };

  const fetchAllReleases = async (jwt: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/press-releases`, {
        headers: { Authorization: `Bearer ${jwt}` },
      });
      if (res.ok) {
        const data = await res.json();
        setReleases(data.reverse());
      } else if (res.status === 401) {
        localStorage.removeItem("token");
        router.push("/login");
      } else {
        showError("Erreur lors du chargement des revues de presse.");
      }
    } catch (err) {
      console.error(err);
      showError("Impossible de se connecter au serveur.");
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (release: PressRelease) => {
    const text = `# ${release.title}\n\n${release.general_summary}\n\n` + 
      release.articles.map(a => `## ${a.title}\n${a.summary}`).join("\n\n");
    navigator.clipboard.writeText(text);
    alert("Copié dans le presse-papier !");
  };

  if (!token) return null;

  return (
    <div className="flex h-screen bg-[#F0F2F5] text-gray-900 font-sans overflow-hidden">
      
      {/* ERROR ALERT */}
      {error && (
        <div className="fixed top-6 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-6 py-3 rounded-xl shadow-2xl z-[200] flex items-center gap-3 animate-[bounce_1s_ease-in-out_infinite]">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm font-bold">{error}</span>
        </div>
      )}

       {/* SIDEBAR */}
       <div className={`fixed inset-y-0 left-0 transform ${isSidebarOpen ? "translate-x-0" : "-translate-x-full"} md:relative md:translate-x-0 transition-transform duration-300 ease-in-out w-64 bg-[#F9F9FB] border-r border-gray-100 flex flex-col z-50 shrink-0`}>
        <div className="h-20 flex items-center px-6 border-b border-gray-50 cursor-pointer" onClick={() => router.push("/")}>
          <Image src="/images/NEWSFOUNDRY.svg" alt="NewsFoundry" width={130} height={24} style={{ filter: 'invert(33%) sepia(87%) saturate(1476%) hue-rotate(242deg) brightness(85%) contrast(100%)' }} />
        </div>

        <div className="flex-1 overflow-y-auto">
          {chats.map((chat) => (
            <div 
              key={chat.id} 
              onClick={() => router.push(`/chat`)}
              className="w-full text-left px-6 py-4 border-b border-gray-50 cursor-pointer hover:bg-gray-50"
            >
              <h3 className="text-sm font-medium text-gray-500">Discussion du</h3>
              <p className="text-[11px] text-gray-400">
                {chat.created_at ? new Date(chat.created_at).toLocaleDateString("fr-FR", { day: '2-digit', month: '2-digit', year: 'numeric' }) : "10/12/2026"}
              </p>
            </div>
          ))}
          {chats.length === 0 && (
            <p className="text-center py-10 text-gray-400 text-sm italic">Aucun historique.</p>
          )}
        </div>

        <div className="p-6 border-t border-gray-100">
          <button onClick={() => { localStorage.removeItem("token"); router.push("/"); }} className="flex items-center gap-2.5 text-gray-500 hover:text-red-500 text-sm font-medium transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
            Se déconnecter
          </button>
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-[#E8E9F1] overflow-y-auto">
        {/* TOP BAR AVEC ONGLETS */}
        <div className="h-20 bg-white border-b border-gray-100 flex items-center px-6 shrink-0">
          <button onClick={() => setIsSidebarOpen(true)} className="md:hidden mr-4">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
          
          <div className="flex bg-[#F3F4F6] p-1 rounded-xl">
            <button 
              onClick={() => router.push("/chat")} 
              className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-bold text-gray-500 hover:text-gray-700 transition-all"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Chat
            </button>
            <button className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-bold bg-[#7B3FE4] text-white shadow-md">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Revue de presse
            </button>
          </div>
        </div>

        {/* CONTENT ACUAL (Revues) */}
        <div className="max-w-5xl w-full mx-auto p-6 md:p-12">
          <div className="mb-10 space-y-1">
            <h2 className="text-[28px] font-bold text-gray-800">Revues de Presse</h2>
            <p className="text-[14px] text-gray-400">Consultez et gérez vos revues de presse générées par l'IA</p>
          </div>

          <div className="space-y-8">
            {isLoading ? (
              <div className="flex justify-center py-20">
                <div className="w-10 h-10 border-4 border-t-purple-600 border-gray-200 rounded-full animate-spin"></div>
              </div>
            ) : releases.length === 0 ? (
              <div className="bg-white rounded-3xl p-16 text-center border-2 border-dashed border-gray-200">
                <p className="text-gray-400 italic">Aucune revue de presse disponible.</p>
              </div>
            ) : (
              releases.map((release, idx) => (
                <div key={idx} className="bg-white rounded-xl shadow-sm border border-gray-50 flex flex-col">
                  {/* Card Header */}
                  <div className="p-6 md:p-8 flex justify-between items-start border-b border-gray-50">
                    <div className="space-y-2">
                      <h3 className="text-[15px] font-bold text-gray-800 uppercase tracking-wide">{release.title}</h3>
                      <div className="flex items-center gap-2 text-[12px] text-gray-400 font-medium">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        {release.created_at 
                          ? new Date(release.created_at).toLocaleDateString("fr-FR", { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }) 
                          : "mardi 30 septembre 2025 à 09:00"}
                      </div>
                    </div>
                    <button 
                      onClick={() => copyToClipboard(release)}
                      className="bg-[#2D2D35] text-white px-6 py-2 rounded-lg text-xs font-bold hover:bg-black transition-all"
                    >
                      Copier
                    </button>
                  </div>

                  {/* Card Body */}
                  <div className="p-8 md:p-10 space-y-6">
                    <div className="text-gray-700 text-base leading-relaxed">
                       <ReactMarkdown>{release.general_summary}</ReactMarkdown>
                    </div>
                    <div className="space-y-6 border-t border-gray-50 pt-6">
                      {release.articles.map((art, aIdx) => (
                        <div key={aIdx} className="space-y-1">
                          <h4 className="font-bold text-gray-800 text-[14px]">**{art.title}**</h4>
                          <p className="text-gray-600 text-[14px] leading-relaxed">{art.summary}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
