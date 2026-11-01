export function computeDistanceMetrics(objA, objB, imgWidth = 960, imgHeight = 600, focalLengthPx = null) {
  if (!objA || !objB) return null;

  const cx1 = objA.centroid?.x ?? (objA.center ? objA.center[0] : 0);
  const cy1 = objA.centroid?.y ?? (objA.center ? objA.center[1] : 0);

  const cx2 = objB.centroid?.x ?? (objB.center ? objB.center[0] : 0);
  const cy2 = objB.centroid?.y ?? (objB.center ? objB.center[1] : 0);

  const dx = cx2 - cx1;
  const dy = cy2 - cy1;
  const pixelDist = Math.sqrt(dx * dx + dy * dy);
  const imgDiag = Math.sqrt(imgWidth * imgWidth + imgHeight * imgHeight);
  const normPct = (pixelDist / (imgDiag || 1)) * 100;
  const f = focalLengthPx || Math.round(imgWidth * 0.9);

  const classHeights = { car: 1.5, person: 1.7, bus: 3.2, bicycle: 1.0, motorcycle: 1.1, truck: 3.0, forklift: 2.2 };
  const hRealA = classHeights[objA.class_name?.toLowerCase()] || 1.5;
  const hRealB = classHeights[objB.class_name?.toLowerCase()] || 1.5;

  const hBoxA = objA.height || 100;
  const hBoxB = objB.height || 100;

  const z1 = (f * hRealA) / Math.max(1, hBoxA);
  const z2 = (f * hRealB) / Math.max(1, hBoxB);

  const cX = imgWidth / 2;
  const cY = imgHeight / 2;

  const x1 = ((cx1 - cX) * z1) / f;
  const y1 = ((cy1 - cY) * z1) / f;
  const x2 = ((cx2 - cX) * z2) / f;
  const y2 = ((cy2 - cY) * z2) / f;

  const dist3D = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2) + Math.pow(z2 - z1, 2));

  return {
    pixel_distance_px: Math.round(pixelDist * 10) / 10,
    pixel_distance: Math.round(pixelDist * 10) / 10,
    delta_x_pixels: Math.abs(dx),
    delta_y_pixels: Math.abs(dy),
    normalized_distance_pct: Math.round(normPct * 10) / 10,
    estimated_relative_distance_m: Math.round(dist3D * 100) / 100,
    focal_length_px: f
  };
}

export const calculateClientDistance = computeDistanceMetrics;
