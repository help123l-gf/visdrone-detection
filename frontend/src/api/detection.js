import request from "../utils/request";

// ── 单图检测 ──
export const detectSingleImage = (data) => {
  return request({
    url: "/detection/single",
    method: "post",
    data,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// ── 批量检测 ──
export const detectBatch = (data) => {
  return request({
    url: "/detection/batch",
    method: "post",
    data,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// ── 视频分析 ──
export const detectVideo = (data) => {
  return request({
    url: "/detection/video",
    method: "post",
    data,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// ── 实时监控帧上传（通过 WebSocket）──
export const detectFrame = (data) => {
  return request({
    url: "/detection/monitor/frame",
    method: "post",
    data,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// ── 检测历史 ──
export const getDetectionHistory = (params) => {
  return request({
    url: "/detection/history",
    method: "get",
    params,
  });
};

// ── 检测详情 ──
export const getDetectionDetail = (id) => {
  return request({
    url: `/detection/detail/${id}`,
    method: "get",
  });
};

// ── 检测统计 ──
export const getDetectionStats = () => {
  return request({
    url: "/detection/stats",
    method: "get",
  });
};

// ── 目标列表 ──
export const getTargetList = () => {
  return request({
    url: "/detection/targets/list",
    method: "get",
  });
};

// ── 删除记录 ──
export const deleteDetectionRecord = (id) => {
  return request({
    url: `/detection/history/${id}`,
    method: "delete",
  });
};
