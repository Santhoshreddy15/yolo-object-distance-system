import React, { useState } from "react";
import { Crosshair, Sliders, Menu, X } from "lucide-react";

export default function Navbar({ isBackendOnline, demoMode, setDemoMode, onScrollTo }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { label: "Vision Studio", id: "demo" },
    { label: "Detection & BBoxes", id: "detection-results" },
    { label: "Distance Measurement", id: "distance-panel" },
  ];

  const handleNavClick = (id) => {
    setMobileMenuOpen(false);
    onScrollTo(id);
  };

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-slate-950/80 border-b border-slate-800/80 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand / Logo */}
        <div 
          onClick={() => handleNavClick("hero")}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-indigo-600 p-0.5 shadow-lg shadow-teal-500/20 group-hover:shadow-teal-500/40 transition-shadow">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Crosshair className="w-5 h-5 text-teal-400 group-hover:rotate-45 transition-transform duration-300" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white group-hover:text-teal-300 transition-colors">
                YOLO-Vision
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20 font-mono">
                AI + Distance
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Computer Vision & Geometric Estimation
            </p>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center gap-1 xl:gap-2 text-xs font-medium text-slate-300">
          {navLinks.map((item) => (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className="px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-slate-800/70 transition-colors"
            >
              {item.label}
            </button>
          ))}
        </nav>

        {/* Backend Status & Mode Toggle */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center">
            {isBackendOnline && !demoMode ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-500/30">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Live YOLO Backend
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-amber-950/60 text-amber-300 border border-amber-500/30">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                Demo / Mock Mode
              </span>
            )}
          </div>

          <button
            onClick={() => setDemoMode(!demoMode)}
            title="Toggle between Live Flask Backend and Mock Demo Mode"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-700 bg-slate-900/90 hover:bg-slate-800 text-slate-200 hover:text-white transition-all shadow-sm"
          >
            <Sliders className="w-3.5 h-3.5 text-teal-400" />
            <span className="hidden md:inline">{demoMode ? "Switch to Live" : "Demo Mode"}</span>
          </button>

          <button
            onClick={() => handleNavClick("demo")}
            className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 text-white shadow-md shadow-teal-500/20 hover:shadow-teal-500/40 transition-all"
          >
            <Crosshair className="w-3.5 h-3.5" />
            Try Demo
          </button>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="lg:hidden px-4 pt-2 pb-4 bg-slate-950/95 border-b border-slate-800 space-y-2 text-sm">
          <div className="grid grid-cols-1 gap-1.5 pt-1">
            {navLinks.map((item) => (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className="text-left px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/80 text-xs transition-colors"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
