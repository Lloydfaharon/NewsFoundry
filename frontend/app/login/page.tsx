import Connexion from "../component/Connexion/Connexion";
import Image from "next/image";

export default function LoginPage() {
  return (
    <div className="relative min-h-screen">
      <Image
        src="/images/bg.jpg"
        alt="Background"
        fill
        className="absolute top-0 left-0 w-full h-full object-cover -z-10"
        priority
      />
      <div className="flex justify-center items-center h-screen z-10 relative px-4 w-full">
        <main className="w-full max-w-md">
          <Connexion />
        </main>
      </div>
    </div>
  );
}
