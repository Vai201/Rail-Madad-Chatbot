import { Outlet } from "react-router";
import { Navigation } from "./Navigation";
import { ChatbotCapsule } from "./ChatbotCapsule";

export function RootLayout() {
  return (
    /* FIX: Added w-full, max-w-full, and overflow-x-hidden.
       This kills the horizontal scroll and that white bar on the right.
    */
    <div className="min-h-screen bg-slate-50 w-full max-w-full overflow-x-hidden relative">
      <Navigation />
      <main className="min-h-screen">
        <Outlet />
      </main>
      <ChatbotCapsule />
    </div>
  );
}