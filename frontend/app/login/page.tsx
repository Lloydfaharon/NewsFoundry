import Connexion from "../component/Connexion/Connexion";
import Image from "next/image";

export default function LoginPage() {
  return (
    <>
      <Image
        src="/images/bg.jpg"
        alt="Background"
        fill
        className="absolute top-0 left-0 w-full h-full object-cover -z-10"
        priority
      />
      <div className="flex justify-center items-center h-screen">
        <main className="">
          <Connexion />
        </main>
      </div>
    </>
  );
}
