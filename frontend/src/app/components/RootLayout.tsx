import { Outlet } from "react-router";
import { Navigation } from "./Navigation";
import { ChatbotCapsule } from "./ChatbotCapsule";

export function RootLayout() {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navigation />
      <main className="min-h-screen">
        <Outlet />
      </main>
      <ChatbotCapsule />
    </div>
  );
}
