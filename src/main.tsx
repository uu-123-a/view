import React, { lazy, Suspense } from "react";
import { createRoot } from "react-dom/client";
import AppErrorBoundary from "./app/AppErrorBoundary";
import AppLoading from "./components/AppLoading";
import "./styles.css";
import "./app-loading.css";

const App = lazy(() => import("./app/App"));

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <Suspense fallback={<AppLoading />}>
        <App />
      </Suspense>
    </AppErrorBoundary>
  </React.StrictMode>,
);
