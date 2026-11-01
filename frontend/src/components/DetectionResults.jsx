import React, { useState } from "react";
import { Table, Crosshair, Percent, Tag, Ruler, Sparkles } from "lucide-react";

export default function DetectionResults({
  resultData,
  selectedObjA,
  selectedObjB,
  setSelectedObjA,
  setSelectedObjB,
  calculatedDistanceResult
}) {
  const [viewMode, setViewMode] = useState("annotated");

  if (!resultData) return null;

  const {
    total_objects = 0,
    inference_time_ms = 0,
    image_dimensions = { width: 960, height: 600 },
    detections = [],
    original_image = "",
    annotated_image = ""
  } = resultData;

  const highestConfidenceDetection = detections.length > 0
    ? [...detections].sort((a, b) => b.confidence - a.confidence)[0]
    : null;

  const currentAnnotatedImg = calculatedDistanceResult?.visualization_image || annotated_image;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="rounded-xl glass-panel p-4 border border-slate-800/90 flex flex-col justify-between">
          <span className="text-xs text-slate-400 font-semibold uppercase">Objects Detected</span>
          <div className="mt-2 text-3xl font-extrabold text-white font-mono">{total_objects}</div>
        </div>

        <div className="rounded-xl glass-panel p-4 border border-slate-800/90 flex flex-col justify-between">
          <span className="text-xs text-slate-400 font-semibold uppercase">Highest Confidence</span>
          <div className="mt-2 text-3xl font-extrabold text-teal-300 font-mono">
            {highestConfidenceDetection ? `${highestConfidenceDetection.confidence_pct}%` : "N/A"}
          </div>
        </div>

        <div className="rounded-xl glass-panel p-4 border border-slate-800/90 flex flex-col justify-between">
          <span className="text-xs text-slate-400 font-semibold uppercase">Selected Object</span>
          <div className="mt-2 text-lg font-bold text-white font-mono truncate">
            {selectedObjA ? `#${selectedObjA.index} ${selectedObjA.class_name}` : "None Selected"}
          </div>
        </div>

        <div className="rounded-xl glass-panel p-4 border border-teal-500/30 bg-teal-950/10 flex flex-col justify-between">
          <span className="text-xs text-teal-400 font-semibold uppercase">Distance</span>
          <div className="mt-2 text-2xl font-black text-teal-300 font-mono">
            {calculatedDistanceResult ? `${calculatedDistanceResult.metrics?.estimated_relative_distance_m} m` : "Select Pair"}
          </div>
        </div>
      </div>

      {/* Visual Canvas Display */}
      <div className="rounded-2xl glass-panel p-4 lg:p-6 border border-slate-800 shadow-2xl">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800 text-xs">
          <span className="font-semibold text-white">Processed Canvas Overlay</span>
          <div className="inline-flex rounded-lg bg-slate-900 p-1 border border-slate-800">
            <button
              onClick={() => setViewMode("annotated")}
              className={`px-3 py-1 rounded text-xs ${viewMode === "annotated" ? "bg-teal-500/20 text-teal-300" : "text-slate-400"}`}
            >
              Annotated
            </button>
            <button
              onClick={() => setViewMode("original")}
              className={`px-3 py-1 rounded text-xs ${viewMode === "original" ? "bg-teal-500/20 text-teal-300" : "text-slate-400"}`}
            >
              Original
            </button>
          </div>
        </div>

        <div className="relative aspect-[16/10] max-h-[580px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center">
          <img
            src={viewMode === "original" ? original_image : currentAnnotatedImg}
            alt="View"
            className="w-full h-full object-contain"
          />
        </div>
      </div>

      {/* Detected Objects Table */}
      <div className="rounded-2xl glass-panel p-5 lg:p-6 border border-slate-800 shadow-xl space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Table className="w-4 h-4 text-teal-400" /> Detected Objects Table
        </h3>

        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px]">
              <tr>
                <th className="px-4 py-3">Object</th>
                <th className="px-4 py-3">Class</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Center X</th>
                <th className="px-4 py-3">Center Y</th>
                <th className="px-4 py-3 text-center">Distance Selection</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 bg-slate-950/40">
              {detections.map((d) => (
                <tr key={d.id} className="hover:bg-slate-800/40">
                  <td className="px-4 py-3 font-bold text-white">#{d.index}</td>
                  <td className="px-4 py-3 text-teal-300 font-semibold">{d.class_name}</td>
                  <td className="px-4 py-3">{d.confidence_pct}%</td>
                  <td className="px-4 py-3">{d.center[0]} px</td>
                  <td className="px-4 py-3">{d.center[1]} px</td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => setSelectedObjA(d)}
                      className={`px-2 py-1 rounded text-[11px] mr-2 ${selectedObjA?.id === d.id ? "bg-teal-500 text-white" : "bg-slate-900 text-slate-300 border border-slate-700"}`}
                    >
                      Set A
                    </button>
                    <button
                      onClick={() => setSelectedObjB(d)}
                      className={`px-2 py-1 rounded text-[11px] ${selectedObjB?.id === d.id ? "bg-indigo-500 text-white" : "bg-slate-900 text-slate-300 border border-slate-700"}`}
                    >
                      Set B
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
