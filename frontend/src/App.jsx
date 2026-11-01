import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import DemoSection from "./components/DemoSection";
import Footer from "./components/Footer";
import { checkBackendHealth } from "./services/api";

export default function App() {
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [demoMode, setDemoMode] = useState(false);

  // Poll backend health status
  useEffect(() => {
    let isMounted = true;

    const checkHealth = async () => {
      try {
        const healthy = await checkBackendHealth();
        if (isMounted) {
          setIsBackendOnline(healthy);
        }
      } catch {
        if (isMounted) {
          setIsBackendOnline(false);
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleScrollTo = (sectionId) => {
    if (sectionId === "hero") {
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    const targetElement = document.getElementById(
      sectionId === "demo" ? "demo-section" : sectionId
    );
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-teal-500 selection:text-slate-950">
      {/* Top Navigation */}
      <Navbar
        isBackendOnline={isBackendOnline}
        demoMode={demoMode}
        setDemoMode={setDemoMode}
        onScrollTo={handleScrollTo}
      />

      <main className="flex-1 space-y-8">
        {/* Hero Section */}
        <Hero onScrollTo={handleScrollTo} />

        {/* Live Studio (Upload / Live Camera / Datasets + YOLO Detections + Distance Panel) */}
        <DemoSection />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
