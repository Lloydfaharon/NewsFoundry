"use client"; // Obligatoire pour utiliser les formulaires et les fonctions React

import Image from "next/image";
import { useState } from "react"; // Pour capter les textes saisis
import { useRouter } from "next/navigation"; // Pour changer de page après connexion

export default function Connexion() {
    // --- 1. LES ÉTATS (Variables qui changent) ---
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    // --- 2. LA LOGIQUE D'ENVOI ---
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault(); // Empêche la page de se recharger
        setIsLoading(true);
        setError("");

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Erreur de connexion");
            }

            // --- 3. STOCKAGE DU TOKEN ---
            localStorage.setItem("token", data.access_token);

            // Redirection vers une page protégée (ex: /dashboard)
            router.push("/");
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-white backdrop-blur-md p-8 rounded-xl shadow-2xl w-full max-w-md p-10 m-20">
            <div className="flex justify-center gap-1">
                <Image src="/images/NEWSFOUNDRY.svg" alt="Logo" width={150} height={150} />
                <Image src="/images/Union-3.svg" alt="Logo" width={20} height={20} />
            </div>

            <h1 className="text text-gray-400 mb-6 mt-6 text-center">
                Connectez-vous pour accéder à votre assistant d'actualités IA
            </h1>

            {/* Affichage de l'erreur si elle existe */}
            {error && <p role="alert" className="text-red-500 text-sm text-center mb-4">{error}</p>}

            <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                    <label htmlFor="email" className="block text-black mb-2">Adresse email</label>
                    <input
                        id="email"
                        type="email"
                        required
                        className="w-full p-2 rounded-lg bg-gray-200 text-black"
                        placeholder="votre.email@exemple.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="password" className="block text-black mb-2">Mot de passe</label>
                    <input
                        id="password"
                        type="password"
                        required
                        className="w-full p-2 rounded-lg bg-gray-200 text-black"
                        placeholder="Mot de passe"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>
                <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 transition-colors"
                >
                    {isLoading ? "Connexion..." : "Se connecter"}
                </button>
            </form>
        </div>
    );
}