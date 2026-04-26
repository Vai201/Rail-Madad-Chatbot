import { createBrowserRouter } from "react-router";
import { RootLayout } from "./components/RootLayout";
import { Home } from "./pages/Home";
import { Trains } from "./pages/Trains";
import { Intent } from "./pages/Intent";
import { Technology } from "./pages/Technology";
import { NotFound } from "./pages/NotFound";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: Home },
      { path: "trains", Component: Trains },
      { path: "intent", Component: Intent },
      { path: "technology", Component: Technology },
      { path: "*", Component: NotFound },
    ],
  },
]);
