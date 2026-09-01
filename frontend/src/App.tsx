import { Route, Routes } from "react-router-dom";

import { ErrorBoundary } from "./components/ErrorBoundary";
import { DetailPage } from "./pages/DetailPage";
import { MainPage } from "./pages/MainPage";

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/spot/:id" element={<DetailPage />} />
      </Routes>
    </ErrorBoundary>
  );
}
