import React from "react";
import { Ruler, Info, CheckCircle2, RefreshCw } from "lucide-react";

export default function DistanceMeasurementPanel({
  detections = [],
  selectedObjA,
  selectedObjB,
  setSelectedObjA,
  setSelectedObjB,
  onCalculateDistance,
  distanceLoading,
  distanceResult,
  onResetDistance
}) {
  const isReady = selectedObjA && selectedObjB && selectedObjA.id !== selectedObjB.id;

  return (
    <div id="distance-panel" className="rounded-2xl glass-panel p-6 sm:p-8 border border-teal-500/30 bg-slate-900/80 shadow-2xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-teal-400 font-semibold tracking-wider text-xs uppercase">
            <Ruler className="w-4 h-4" />
            <span>Interactive Spatial Analysis</span>
          </div>
          <h3 className="text-xl sm:text-2xl font-bold text-white mt-1">
            Distance Estimation Panel
          </h3>
          <p className="text-sm text-slate-400 mt-1">
            Select two detected objects to estimate relative spatial distance using Euclidean centroids and monocular camera geometry.
          </p>
        </div>

        {distanceResult && (
          <button
            onClick={onResetDistance}
            className="flex items-center gap-2 px-3 py-2 text-xs font-semibold text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 rounded-lg transition-all border border-slate-700"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset Selection
          </button>
        )}
      </div>

      {detections.length < 2 ? (
        <div className="p-6 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-sm flex items-start gap-3">
          <Info className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">At least 2 detected objects are required</span> to calculate relative distance. Try uploading an image with multiple objects or test with one of the multi-object sample scenes above.
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Object A selector */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-teal-400 flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center text-[10px] font-black border border-teal-500/40">1</span>
                Select Object A
              </label>
              {selectedObjA && (
                <span className="text-[11px] font-mono text-teal-300 bg-teal-950/80 px-2 py-0.5 rounded border border-teal-500/30">
                  ID: #{selectedObjA.index}
                </span>
              )}
            </div>
            <select
              value={selectedObjA ? selectedObjA.id : ""}
              onChange={(e) => {
                const found = detections.find((d) => d.id === e.target.value);
                setSelectedObjA(found || null);
              }}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-teal-500"
            >
              <option value="">-- Choose first object --</option>
              {detections.map((d) => (
                <option key={`a-${d.id}`} value={d.id} disabled={selectedObjB?.id === d.id}>
                  #{d.index} {d.class_name} ({d.confidence_pct}%) - center: [{d.centroid?.x}, {d.centroid?.y}]
                </option>
              ))}
            </select>
            {selectedObjA && (
              <div className="text-xs text-slate-400 space-y-1 pt-1 font-mono">
                <div>Class: <span className="text-white font-medium">{selectedObjA.class_name}</span></div>
                <div>Confidence: <span className="text-teal-400 font-medium">{selectedObjA.confidence_pct}%</span></div>
                <div>Bounding Box: <span className="text-slate-300">[{selectedObjA.box_coords?.join(", ")}]</span></div>
              </div>
            )}
          </div>

          {/* Object B selector */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-teal-400 flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center text-[10px] font-black border border-teal-500/40">2</span>
                Select Object B
              </label>
              {selectedObjB && (
                <span className="text-[11px] font-mono text-teal-300 bg-teal-950/80 px-2 py-0.5 rounded border border-teal-500/30">
                  ID: #{selectedObjB.index}
                </span>
              )}
            </div>
            <select
              value={selectedObjB ? selectedObjB.id : ""}
              onChange={(e) => {
                const found = detections.find((d) => d.id === e.target.value);
                setSelectedObjB(found || null);
              }}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-teal-500"
            >
              <option value="">-- Choose second object --</option>
              {detections.map((d) => (
                <option key={`b-${d.id}`} value={d.id} disabled={selectedObjA?.id === d.id}>
                  #{d.index} {d.class_name} ({d.confidence_pct}%) - center: [{d.centroid?.x}, {d.centroid?.y}]
                </option>
              ))}
            </select>
            {selectedObjB && (
              <div className="text-xs text-slate-400 space-y-1 pt-1 font-mono">
                <div>Class: <span className="text-white font-medium">{selectedObjB.class_name}</span></div>
                <div>Confidence: <span className="text-teal-400 font-medium">{selectedObjB.confidence_pct}%</span></div>
                <div>Bounding Box: <span className="text-slate-300">[{selectedObjB.box_coords?.join(", ")}]</span></div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Calculate Button */}
      {detections.length >= 2 && (
        <div className="flex justify-center pt-2">
          <button
            onClick={onCalculateDistance}
            disabled={!isReady || distanceLoading}
            className={`px-8 py-3.5 rounded-xl font-bold flex items-center gap-3 text-sm transition-all shadow-lg ${
              isReady && !distanceLoading
                ? "bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 hover:from-teal-400 hover:to-cyan-400 cursor-pointer shadow-teal-500/20 hover:scale-[1.02]"
                : "bg-slate-800 text-slate-500 cursor-not-allowed"
            }`}
          >
            {distanceLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                <span>Computing Geometry & Distance...</span>
              </>
            ) : (
              <>
                <Ruler className="w-5 h-5" />
                <span>Calculate Distance</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Distance Result Display */}
      {distanceResult && (
        <div className="p-5 sm:p-6 rounded-2xl bg-teal-950/20 border border-teal-500/40 space-y-5 animate-fadeIn">
          <div className="flex items-center gap-2 text-teal-400 font-bold text-sm uppercase tracking-wider">
            <CheckCircle2 className="w-5 h-5 text-teal-400" />
            <span>Estimated Relative Distance Result</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/90 border border-teal-500/30">
              <span className="text-xs text-slate-400 font-medium">Estimated Relative Distance</span>
              <div className="text-3xl font-black text-teal-300 font-mono mt-1">
                {distanceResult.metrics?.estimated_relative_distance_m} <span className="text-lg font-normal text-slate-400">m</span>
              </div>
              <span className="text-[11px] text-slate-500 block mt-1">Monocular pinhole depth projection</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
              <span className="text-xs text-slate-400 font-medium">2D Pixel Distance</span>
              <div className="text-3xl font-black text-white font-mono mt-1">
                {distanceResult.metrics?.pixel_distance_px} <span className="text-lg font-normal text-slate-400">px</span>
              </div>
              <span className="text-[11px] text-slate-500 block mt-1">Euclidean centroid separation</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
              <span className="text-xs text-slate-400 font-medium">Selected Pair</span>
              <div className="text-base font-bold text-slate-200 mt-2 truncate">
                {distanceResult.object_a?.class_name} ({distanceResult.object_a?.id})
                <span className="text-teal-400 mx-2">↔</span>
                {distanceResult.object_b?.class_name} ({distanceResult.object_b?.id})
              </div>
              <span className="text-[11px] text-slate-500 block mt-1">Calculated via Flask CV Engine</span>
            </div>
          </div>

          {/* Technical Note / Disclaimer from PPT */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 space-y-2">
            <div className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-teal-400" />
              Geometric Formulation & Calibration Disclaimer
            </div>
            <p>
              As outlined in the project presentation, distance estimation combines detected object bounding-box coordinates, centroid coordinates, and pinhole camera geometric principles:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-[11px] bg-slate-900 p-2.5 rounded border border-slate-800 text-teal-300">
              <div>Centroid: C = ((x1 + x2)/2, (y1 + y2)/2)</div>
              <div>Pixel Distance: d = √[(Δx)² + (Δy)²]</div>
              <div>Depth Estimate: Z ≈ (f · H_real) / h_box</div>
              <div>Relative Distance: D ≈ √[(ΔX)² + (ΔY)² + (ΔZ)²]</div>
            </div>
            <p className="text-slate-400 text-[11px]">
              *Note: Results are explicitly designated as <strong>Estimated Relative Distance</strong>. Physical distance requires camera intrinsic calibration (focal length f) and reference object physical dimensions (H_real).
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
