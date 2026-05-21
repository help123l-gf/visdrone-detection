import request from "../utils/request";

// ── 单图检测（已实现）──
export const detectSingleImage = (data) => {
  return request({
    url: "/detection/single",
    method: "post",
    data,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// ── 批量检测（后端 TODO）──
export const detectBatch = (data) => {
  return request({
    url: "/detection/batch",
    method: "post",
    data,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// ── 视频分析（后端 TODO）──
export const detectVideo = (data) => {
  return request({
    url: "/detection/video",
    method: "post",
    data,
    headers: { "Content-Type": "multipart/form-data" },
    // 返回逐帧检测结果: { frames: [{ timestamp, boxes }] }
  });
};

// ── 实时监控帧上传（后端 TODO）──
export const detectFrame = (data) => {
  return request({
    url: "/detection/monitor/frame",
    method: "post",
    data,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// ── 检测历史（后端 TODO）──
export const getDetectionHistory = (params) => {
  return request({
    url: "/detection/history",
    method: "get",
    params,
    // params: { keyword, type, congestion, startDate, endDate, page, pageSize }
  });
};

// ── 检测详情 ──
export const getDetectionDetail = (id) => {
  return request({
    url: `/detection/detail/${id}`,
    method: "get",
  });
};

// ── 目标列表 ──
export const getTargetList = () => {
  return request({
    url: "/targets/list",
    method: "get",
  });
};
