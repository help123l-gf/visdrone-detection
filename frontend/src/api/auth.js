import request from "../utils/request";

// 登录
export const login = (data) => {
  return request({
    url: "/auth/login",
    method: "post",
    data,
  });
};

// 注册
export const register = (data) => {
  return request({
    url: "/auth/register",
    method: "post",
    data,
  });
};

// 忘记密码
export const forgotPassword = (data) => {
  return request({
    url: "/auth/forgot-password",
    method: "post",
    data,
  });
};
