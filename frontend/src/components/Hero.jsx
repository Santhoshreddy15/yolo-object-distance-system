import React from "react";
import { Crosshair, ArrowRight, Layers, Sparkles } from "lucide-react";

export default function Hero({ onScrollTo }) {
  return (
    <section id="hero" className="relative pt-12 pb-20 md:py-24 overflow-hidden cyber-grid border-b border-slate-900">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[350px] bg-gradient-to-tr from-teal-500/15 via-indigo-600/15 to-transparent blur-[120px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-teal-500/30 text-teal-300 text-xs font-medium shadow-sm">
              <Sparkles className="w-3.5 h-3.5 text-teal-400" />
              <span>Domain: Artificial Intelligence & Computer Vision</span>
              <span className="w-1 h-1 rounded-full bg-slate-600" />
              <span className="text-slate-400">Static Image Analysis</span>
            </div>

            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.15]">
              YOLO-Based Object Detection{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 via-teal-200 to-indigo-400">
                & Distance Measurement
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto lg:mx-0 font-normal leading-relaxed">
              Detect objects, visualize their locations, and estimate relative distance using computer vision.
            </p>

            <div className="flex flex-col sm:flex-row gap-3.5 pt-4 justify-center lg:justify-start">
              <button
                onClick={() => onScrollTo("demo")}
                className="inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-teal-500 via-teal-600 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 shadow-xl shadow-teal-500/25 transition-all transform hover:-translate-y-0.5"
              >
                <Crosshair className="w-4 h-4" />
                Try Object Detection
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>

              <button
                onClick={() => onScrollTo("distance-panel")}
                className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-semibold text-slate-200 bg-slate-900/90 hover:bg-slate-800/90 border border-slate-700/80 shadow-sm transition-all"
              >
                <Layers className="w-4 h-4 text-teal-400" />
                Distance Measurement Studio
              </button>
            </div>
          </div>

          <div className="lg:col-span-5">
            <div className="relative rounded-2xl glass-panel p-4 md:p-5 shadow-2xl border border-slate-700/60">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800/80 text-xs">
                <span className="font-mono text-slate-400 text-[11px]">Computer Vision HUD Preview</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  Visual Demonstration
                </span>
              </div>
              <div className="relative aspect-[16/10] bg-slate-900/90 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center">
                <div className="text-center p-6 space-y-2">
                  <Crosshair className="w-10 h-10 text-teal-400 mx-auto animate-pulse" />
                  <p className="text-xs text-slate-300 font-mono">BBoxes • Centroids • Monocular Depth</p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
