import React from "react";
import { Eye, ShieldCheck, Sparkles, Terminal } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950/80 backdrop-blur-md py-8 px-4 sm:px-6 lg:px-8 mt-16 text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
            <Eye className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-white text-sm">YOLO CV Studio</span>
            <span className="block text-[11px] text-slate-500">
              Object Detection & Estimated Distance Measurement
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-slate-400 text-[11px]">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
            Static Image Analysis Focused
          </span>
          <span className="text-slate-700">•</span>
          <span className="flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            Flask REST API Backend (Port 5000)
          </span>
          <span className="text-slate-700">•</span>
          <span className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-teal-300" />
            Vite React Frontend
          </span>
        </div>

        <div className="text-slate-500 text-[11px]">
          &copy; {new Date().getFullYear()} YOLO Distance Measurement System. Academic & Research CV Prototype.
        </div>
      </div>
    </footer>
  );
}
