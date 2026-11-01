export const MOCK_DETECTION_RESULT = {
  success: true,
  is_mock: true,
  model_used: "yolov8n.pt (Simulation Mode)",
  inference_time_ms: 18.2,
  image_dimensions: { width: 960, height: 600 },
  total_objects: 3,
  classes_detected: ["car", "bus", "person"],
  detections: [
    {
      id: "obj_1",
      index: 1,
      class_name: "car",
      class_id: 2,
      confidence: 0.942,
      confidence_pct: 94.2,
      box_coords: [140, 360, 400, 500],
      bbox: [140, 360, 400, 500],
      center: [270, 430],
      centroid: { x: 270, y: 430 },
      width: 260,
      height: 140,
      bottom_center: [270, 500]
    },
    {
      id: "obj_2",
      index: 2,
      class_name: "car",
      class_id: 2,
      confidence: 0.887,
      confidence_pct: 88.7,
      box_coords: [580, 310, 790, 420],
      bbox: [580, 310, 790, 420],
      center: [685, 365],
      centroid: { x: 685, y: 365 },
      width: 210,
      height: 110,
      bottom_center: [685, 420]
    },
    {
      id: "obj_3",
      index: 3,
      class_name: "person",
      class_id: 0,
      confidence: 0.845,
      confidence_pct: 84.5,
      box_coords: [846, 320, 874, 460],
      bbox: [846, 320, 874, 460],
      center: [860, 390],
      centroid: { x: 860, y: 390 },
      width: 28,
      height: 140,
      bottom_center: [860, 460]
    }
  ]
};

export const mockDetectionData = {
  traffic_urban: {
    ...MOCK_DETECTION_RESULT
  },
  pedestrian_crossing: {
    ...MOCK_DETECTION_RESULT,
    total_objects: 2,
    detections: [
      MOCK_DETECTION_RESULT.detections[0],
      MOCK_DETECTION_RESULT.detections[2]
    ]
  },
  warehouse_robotics: {
    ...MOCK_DETECTION_RESULT,
    total_objects: 2,
    detections: [
      {
        id: "obj_w1",
        index: 1,
        class_name: "forklift",
        class_id: 8,
        confidence: 0.92,
        confidence_pct: 92.0,
        box_coords: [200, 250, 480, 520],
        bbox: [200, 250, 480, 520],
        center: [340, 385],
        centroid: { x: 340, y: 385 },
        width: 280,
        height: 270
      },
      {
        id: "obj_w2",
        index: 2,
        class_name: "person",
        class_id: 0,
        confidence: 0.87,
        confidence_pct: 87.0,
        box_coords: [620, 300, 680, 500],
        bbox: [620, 300, 680, 500],
        center: [650, 400],
        centroid: { x: 650, y: 400 },
        width: 60,
        height: 200
      }
    ]
  }
};
