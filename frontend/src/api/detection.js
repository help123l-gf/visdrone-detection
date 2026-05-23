import request from "../utils/request";

// Single
export const detectSingleImage = (data) => request({ url: "/detection/single", method: "post", data, headers: { "Content-Type": "multipart/form-data" } });

// Batch
export const detectBatch = (data) => request({ url: "/detection/batch", method: "post", data, headers: { "Content-Type": "multipart/form-data" } });

// Video
export const detectVideo = (data) => request({ url: "/detection/video", method: "post", data, headers: { "Content-Type": "multipart/form-data" }, timeout: 600000 });

// History
export const getDetectionHistory = (params) => request({ url: "/detection/history", method: "get", params });

// Detail
export const getDetectionDetail = (id) => request({ url: `/detection/detail/${id}`, method: "get" });

// Targets
export const getTargetList = () => request({ url: "/targets/list", method: "get" });

// Auth
export const login = (data) => request({ url: "/auth/login", method: "post", data });
export const register = (data) => request({ url: "/auth/register", method: "post", data });
export const getProfile = () => request({ url: "/auth/me", method: "get" });
export const getStats = () => request({ url: "/auth/stats", method: "get" });

// Download
export const downloadResults = (recordIds) => request({ url: "/detection/download", method: "get", params: { record_ids: recordIds }, responseType: "blob" });

// Delete
export const deleteRecord = (id) => request({ url: `/detection/delete/${id}`, method: "delete" });
