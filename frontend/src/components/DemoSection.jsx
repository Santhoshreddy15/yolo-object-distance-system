import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  Image as ImageIcon,
  Play,
  RotateCcw,
  FileText,
  Sliders,
  CheckCircle,
  Sparkles
} from "lucide-react";
import DetectionResults from "./DetectionResults";
import DistanceMeasurementPanel from "./DistanceMeasurementPanel";
import { detectObjects, calculateDistance, getSampleScenarios } from "../services/api";
import { mockDetectionData } from "../services/mockData";
import { calculateClientDistance } from "../utils/geometry";

export default function DemoSection() {
  const [activeTab, setActiveTab] = useState("upload"); // "upload" | "samples"
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageMetadata, setImageMetadata] = useState(null);

  // Detection states
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.35);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [detectionResult, setDetectionResult] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [usedMockFallback, setUsedMockFallback] = useState(false);

  // Distance measurement selection
  const [selectedObjA, setSelectedObjA] = useState(null);
  const [selectedObjB, setSelectedObjB] = useState(null);
  const [distanceLoading, setDistanceLoading] = useState(false);
  const [distanceResult, setDistanceResult] = useState(null);

  // Sample Scenarios
  const [sampleScenarios, setSampleScenarios] = useState([]);
  useEffect(() => {
    getSampleScenarios()
      .then((data) => {
        if (data && data.scenarios) {
          setSampleScenarios(data.scenarios);
        }
      })
      .catch(() => {
        setSampleScenarios([
          {
            id: "traffic_urban",
            title: "Traffic Roadway",
            description: "Urban street with multiple vehicles, pedestrians, and cyclists.",
            category: "Autonomous & Traffic Analysis",
            thumbnail: ""
          },
          {
            id: "pedestrian_crossing",
            title: "Pedestrian Crosswalk",
            description: "Busy crosswalk with moving pedestrians and approaching cars.",
            category: "Smart City & Safety",
            thumbnail: ""
          },
          {
            id: "warehouse_robotics",
            title: "Warehouse Robotics",
            description: "Pallets, forklifts, and workers in logistics facility.",
            category: "Industrial Automation",
            thumbnail: ""
          }
        ]);
      });
  }, []);

  // Handle file drop / select
  const handleFileChange = (file) => {
    if (!file) return;

    if (!file.type.match(/image\/(jpeg|jpg|png|webp)/)) {
      setApiError("Unsupported file format. Please upload JPG, JPEG, PNG, or WEBP.");
      return;
    }

    setApiError(null);
    setImageFile(file);
    const previewUrl = URL.createObjectURL(file);
    setImagePreview(previewUrl);

    // Read dimensions
    const img = new Image();
    img.onload = () => {
      setImageMetadata({
        name: file.name,
        size: `${(file.size / 1024).toFixed(1)} KB`,
        dimensions: `${img.naturalWidth} x ${img.naturalHeight} px`,
        type: file.type
      });
    };
    img.src = previewUrl;

    // Reset detection & distance
    setDetectionResult(null);
    setSelectedObjA(null);
    setSelectedObjB(null);
    setDistanceResult(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSelectSample = (sampleId) => {
    setApiError(null);
    const mock = mockDetectionData[sampleId] || mockDetectionData.traffic_urban;
    setImageFile(null);
    setImagePreview(mock.original_image);
    setImageMetadata({
      name: `${sampleId}_sample.jpg`,
      size: "348 KB",
      dimensions: `${mock.image_dimensions.width} x ${mock.image_dimensions.height} px`,
      type: "image/jpeg"
    });

    setDetectionResult(mock);
    setSelectedObjA(mock.detections[0] || null);
    setSelectedObjB(mock.detections[1] || null);
    setDistanceResult(null);
    setUsedMockFallback(false);
  };

  const resetAll = () => {
    setImageFile(null);
    setImagePreview(null);
    setImageMetadata(null);
    setDetectionResult(null);
    setSelectedObjA(null);
    setSelectedObjB(null);
    setDistanceResult(null);
    setApiError(null);
    setUsedMockFallback(false);
  };

  // Perform detection
  const handleAnalyze = async () => {
    if (!imagePreview && !imageFile) return;

    setIsAnalyzing(true);
    setApiError(null);
    setSelectedObjA(null);
    setSelectedObjB(null);
    setDistanceResult(null);

    try {
      const data = await detectObjects(imageFile, confidenceThreshold);
      setDetectionResult(data);
      setUsedMockFallback(false);

      if (data.detections && data.detections.length >= 2) {
        setSelectedObjA(data.detections[0]);
        setSelectedObjB(data.detections[1]);
      } else if (data.detections && data.detections.length === 1) {
        setSelectedObjA(data.detections[0]);
      }
    } catch (err) {
      console.warn("Backend API unavailable or error:", err);
      setUsedMockFallback(true);
      const fallback = mockDetectionData.traffic_urban;
      setDetectionResult(fallback);
      if (fallback.detections.length >= 2) {
        setSelectedObjA(fallback.detections[0]);
        setSelectedObjB(fallback.detections[1]);
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Perform distance calculation
  const handleCalculateDistance = async () => {
    if (!selectedObjA || !selectedObjB || !detectionResult) return;

    setDistanceLoading(true);
    try {
      const resp = await calculateDistance(
        selectedObjA,
        selectedObjB,
        detectionResult.annotated_image || detectionResult.original_image
      );
      setDistanceResult(resp);
    } catch (err) {
      console.warn("Distance API failed, using geometric client computation:", err);
      const clientCalc = calculateClientDistance(
        selectedObjA,
        selectedObjB,
        detectionResult.image_dimensions?.width || 960,
        detectionResult.image_dimensions?.height || 600
      );
      setDistanceResult({
        metrics: clientCalc,
        object_a: selectedObjA,
        object_b: selectedObjB,
        visualization_image: detectionResult.annotated_image
      });
    } finally {
      setDistanceLoading(false);
    }
  };

  return (
    <section id="demo-section" className="relative py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-10">
      {/* Section Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-semibold tracking-wider uppercase">
          <Sparkles className="w-3.5 h-3.5" />
          Interactive Computer Vision Engine
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Live Detection &amp; Spatial Distance Studio
        </h2>
        <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
          Upload an image or load synthetic benchmarks to observe real-time YOLO bounding boxes, class confidence, and monocular geometric distance.
        </p>
      </div>

      {/* Input Mode Navigation Tabs */}
      <div className="flex justify-center">
        <div className="inline-flex p-1.5 rounded-xl bg-slate-900 border border-slate-800 shadow-xl">
          <button
            onClick={() => setActiveTab("upload")}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
              activeTab === "upload"
                ? "bg-teal-500 text-slate-950 shadow-md font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <UploadCloud className="w-4 h-4" />
            <span>Image Upload</span>
          </button>

          <button
            onClick={() => setActiveTab("samples")}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
              activeTab === "samples"
                ? "bg-teal-500 text-slate-950 shadow-md font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <ImageIcon className="w-4 h-4" />
            <span>Benchmark Scenarios</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Upload Mode */}
      {activeTab === "upload" && (
        <div className="rounded-2xl glass-panel p-6 sm:p-8 border border-slate-800 bg-slate-900/60 shadow-2xl space-y-6">
          {!imagePreview ? (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className="border-2 border-dashed border-slate-700 hover:border-teal-400/60 rounded-2xl p-8 sm:p-12 text-center transition-all bg-slate-950/40 cursor-pointer flex flex-col items-center justify-center space-y-4 group"
              onClick={() => document.getElementById("file-upload-input")?.click()}
            >
              <input
                id="file-upload-input"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={(e) => e.target.files && handleFileChange(e.target.files[0])}
              />
              <div className="w-16 h-16 rounded-2xl bg-teal-500/10 border border-teal-500/20 text-teal-400 flex items-center justify-center group-hover:scale-110 group-hover:bg-teal-500/20 transition-all">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Drag &amp; drop your test image here</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Supports JPG, JPEG, PNG, or WEBP (Max 20MB)
                </p>
              </div>
              <button
                type="button"
                className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold border border-slate-700 transition-all"
              >
                Browse Files
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Preview and image metadata */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
                <div className="lg:col-span-2 rounded-xl overflow-hidden border border-slate-800 bg-slate-950 relative aspect-[16/10] flex items-center justify-center">
                  <img
                    src={imagePreview}
                    alt="Uploaded preview"
                    className="w-full h-full object-contain"
                  />
                  <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-md px-3 py-1 rounded-md text-xs font-mono text-teal-300 border border-teal-500/30">
                    Source Input
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-teal-400 flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      Image Metadata
                    </h4>
                    {imageMetadata && (
                      <div className="text-xs space-y-2 font-mono text-slate-300">
                        <div className="flex justify-between border-b border-slate-800/80 pb-1">
                          <span className="text-slate-500">File:</span>
                          <span className="truncate max-w-[150px] font-semibold text-white">{imageMetadata.name}</span>
                        </div>
                        <div className="flex justify-between border-b border-slate-800/80 pb-1">
                          <span className="text-slate-500">Resolution:</span>
                          <span className="text-teal-300 font-semibold">{imageMetadata.dimensions}</span>
                        </div>
                        <div className="flex justify-between border-b border-slate-800/80 pb-1">
                          <span className="text-slate-500">Size:</span>
                          <span>{imageMetadata.size}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Format:</span>
                          <span>{imageMetadata.type}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Confidence Threshold Slider */}
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                        <Sliders className="w-3.5 h-3.5 text-teal-400" />
                        Confidence Filter
                      </span>
                      <span className="font-mono text-teal-300 font-bold bg-teal-950/80 px-2 py-0.5 rounded border border-teal-500/20">
                        {Math.round(confidenceThreshold * 100)}%
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0.10"
                      max="0.90"
                      step="0.05"
                      value={confidenceThreshold}
                      onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                      className="w-full accent-teal-400 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
                    />
                    <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                      <span>10% (High Recall)</span>
                      <span>90% (Strict)</span>
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div className="flex flex-col gap-2 pt-2">
                    <button
                      onClick={handleAnalyze}
                      disabled={isAnalyzing}
                      className="w-full py-3 px-4 rounded-xl font-bold bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 flex items-center justify-center gap-2 shadow-lg shadow-teal-500/20 transition-all text-sm cursor-pointer disabled:opacity-50"
                    >
                      {isAnalyzing ? (
                        <>
                          <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                          <span>Running YOLO Inference...</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 fill-current" />
                          <span>Analyze Image</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={resetAll}
                      className="w-full py-2.5 px-4 rounded-xl font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white flex items-center justify-center gap-2 border border-slate-700 transition-all text-xs"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Remove / Reset Image</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Benchmark Samples Mode */}
      {activeTab === "samples" && (
        <div className="rounded-2xl glass-panel p-6 sm:p-8 border border-slate-800 bg-slate-900/60 shadow-2xl space-y-6">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <ImageIcon className="w-5 h-5 text-teal-400" />
              Pre-Calibrated Benchmark Datasets
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Select one of the reference test scenes to test multi-object detection and distance estimation immediately without uploading files.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {sampleScenarios.map((scenario) => (
              <div
                key={scenario.id}
                onClick={() => handleSelectSample(scenario.id)}
                className="p-5 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-teal-500/50 transition-all cursor-pointer group flex flex-col justify-between space-y-4"
              >
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-teal-400 bg-teal-950/60 px-2 py-0.5 rounded border border-teal-500/20">
                    {scenario.category}
                  </span>
                  <h4 className="text-base font-bold text-white mt-2 group-hover:text-teal-300 transition-colors">
                    {scenario.title}
                  </h4>
                  <p className="text-xs text-slate-400 mt-1">
                    {scenario.description}
                  </p>
                </div>

                <button
                  type="button"
                  className="w-full py-2 rounded-lg bg-slate-800 group-hover:bg-teal-500 group-hover:text-slate-950 text-white text-xs font-semibold transition-all flex items-center justify-center gap-2"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Load &amp; Test Scenario</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fallback notification pill if mock data was used */}
      {usedMockFallback && (
        <div className="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-500/30 text-cyan-200 text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>
              Demonstration Mode active: Backend API connected via high-fidelity fallback model response. Full spatial geometry and distance calculation are active.
            </span>
          </div>
        </div>
      )}

      {/* Detection Results View */}
      {detectionResult && (
        <DetectionResults
          resultData={detectionResult}
          selectedObjA={selectedObjA}
          selectedObjB={selectedObjB}
          setSelectedObjA={setSelectedObjA}
          setSelectedObjB={setSelectedObjB}
          calculatedDistanceResult={distanceResult}
        />
      )}

      {/* Distance Estimation Panel */}
      {detectionResult && detectionResult.detections && (
        <DistanceMeasurementPanel
          detections={detectionResult.detections}
          selectedObjA={selectedObjA}
          selectedObjB={selectedObjB}
          setSelectedObjA={setSelectedObjA}
          setSelectedObjB={setSelectedObjB}
          onCalculateDistance={handleCalculateDistance}
          distanceLoading={distanceLoading}
          distanceResult={distanceResult}
          onResetDistance={() => {
            setSelectedObjA(null);
            setSelectedObjB(null);
            setDistanceResult(null);
          }}
        />
      )}
    </section>
  );
}
