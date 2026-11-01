const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api";

export async function checkBackendHealth() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);
    const response = await fetch(`${API_BASE_URL}/health`, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (!response.ok) return false;
    const data = await response.json();
    return data.status === "healthy" || data.status === "ok" || response.ok;
  } catch (err) {
    return false;
  }
}

export async function detectObjects(fileOrBase64, conf = 0.35, iou = 0.45) {
  let response;
  if (fileOrBase64 instanceof File || fileOrBase64 instanceof Blob) {
    const formData = new FormData();
    formData.append("image", fileOrBase64);
    formData.append("conf", conf);
    formData.append("iou", iou);
    response = await fetch(`${API_BASE_URL}/detect`, { method: "POST", body: formData });
  } else if (typeof fileOrBase64 === "string" && fileOrBase64.startsWith("data:image")) {
    response = await fetch(`${API_BASE_URL}/detect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_base64: fileOrBase64, conf, iou })
    });
  } else {
    response = await fetch(`${API_BASE_URL}/detect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conf, iou })
    });
  }

  if (!response.ok) {
    throw new Error(`Detection request failed with status: ${response.status}`);
  }
  return await response.json();
}

export async function calculateDistance(objA, objB, imageBase64 = null) {
  const payload = {
    object_a: objA,
    object_b: objB,
    image_base64: imageBase64
  };
  const response = await fetch(`${API_BASE_URL}/distance`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`Distance request failed with status: ${response.status}`);
  }
  return await response.json();
}

export async function getSampleScenarios() {
  return {
    scenarios: [
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
        title: "Warehouse Logistics",
        description: "Pallets, forklifts, and workers in logistics facility.",
        category: "Industrial Automation",
        thumbnail: ""
      }
    ]
  };
}
