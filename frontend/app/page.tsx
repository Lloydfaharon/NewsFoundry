"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function Home() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Vérification basique du token
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login"); // Redirection s'il n'est pas connecté
    } else {
      setIsAuthenticated(true);
    }
  }, [router]);

  // Écran de chargement esthétique en attendant la vérification
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-10 h-10 rounded-full border-4 border-t-blue-500 border-zinc-800 animate-spin"></div>
      </div>
    );
  }

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center overflow-hidden bg-black text-white font-sans">
      {/* Éléments de fond dynamiques et floutés (Glassmorphism + animations) */}
      <div className="absolute inset-0 z-0">
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-blue-600/20 blur-[100px] animate-pulse"></div>
        <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-purple-600/20 blur-[100px] animate-pulse" style={{ animationDelay: "2s" }}></div>
      </div>

      {/* Carte Centrale */}
      <div className="relative z-10 w-full max-w-xl p-4">
        {/* Bordure lumineuse derrière la carte */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/30 via-transparent to-purple-500/30 rounded-3xl blur-xl opacity-60"></div>

        {/* Contenu de la carte (effet verre / translucide) */}
        <div className="relative bg-zinc-900/60 backdrop-blur-2xl border border-white/5 p-12 sm:p-16 rounded-3xl shadow-2xl text-center flex flex-col items-center">

          {/* Icône de succès animée */}
          <div className="w-24 h-24 mb-6 bg-gradient-to-tr from-green-400 to-emerald-600 rounded-full flex items-center justify-center shadow-[0_0_50px_rgba(52,211,153,0.3)] animate-bounce" style={{ animationDuration: "3s" }}>
            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
            Vous êtes connecté !
          </h1>
          <div>
            <p className="text-zinc-400 text-lg mb-10 leading-relaxed max-w-sm">
              Bienvenue sur votre espace de travail intelligent
            </p>
            <div className="flex justify-center items-center gap-2 mt-4 opacity-80">
              <Image src="/images/NEWSFOUNDRY.svg" alt="NewsFoundry" width={120} height={20} />
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="group relative w-full sm:w-auto px-8 py-3 rounded-full overflow-hidden bg-zinc-800 border border-zinc-700 hover:border-red-500/50 transition-all duration-300 shadow-lg"
          >
            {/* Effet au survol (bouton se remplit de rouge) */}
            <div className="absolute inset-0 w-0 bg-gradient-to-r from-red-600 to-rose-500 transition-all duration-500 ease-out group-hover:w-full"></div>
            <span className="relative flex items-center justify-center gap-2 text-zinc-300 font-medium group-hover:text-white transition-colors duration-300">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Se déconnecter
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
