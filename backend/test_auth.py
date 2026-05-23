import urllib.request, json

BASE = "http://localhost:8000/api/auth"

def post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

# 1. 注册
print("=== 1. 注册 ===")
code, res = post(BASE + "/register", {"username": "admin", "email": "admin@visdrone.cn", "password": "admin123"})
print(f"状态码: {code}")
print(f"success: {res.get('success')}, message: {res.get('message')}")

# 2. 登录
print("\n=== 2. 登录 ===")
code, res = post(BASE + "/login", {"username": "admin", "password": "admin123"})
print(f"状态码: {code}")
print(f"token: {res.get('token', '')[:60]}...")
print(f"user: {res.get('user')}")

# 3. 错误密码
print("\n=== 3. 错误密码 ===")
code, res = post(BASE + "/login", {"username": "admin", "password": "wrong"})
print(f"状态码: {code}, detail: {res.get('detail')}")

# 4. 忘记密码
print("\n=== 4. 忘记密码 ===")
code, res = post(BASE + "/forgot-password", {"email": "admin@visdrone.cn"})
print(f"状态码: {code}, message: {res.get('message')}")

print("\n=== 全部测试完成 ===")
