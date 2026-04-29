import { redirect } from 'next/navigation';
export default function Home() {
  redirect('/login'); // Redirige instantanément vers la page de connexion
}