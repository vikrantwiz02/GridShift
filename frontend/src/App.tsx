import { BrowserRouter, Route, Routes } from "react-router-dom";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import Dashboard from "@/pages/Dashboard";
import SchedulePage from "@/pages/SchedulePage";
import CertificatesPage from "@/pages/CertificatesPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-950">
        <Sidebar />
        <div className="flex flex-col flex-1 overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-auto p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/schedule" element={<SchedulePage />} />
              <Route path="/certificates" element={<CertificatesPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
