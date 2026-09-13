import http.server
import socketserver
import json
import os
import sys

PORT = 8787
mock_kv = {
    "sub:sample-sub": json.dumps({
        "sourceUrl": "https://example.com/api/v1/client/subscribe?token=demo_token",
        "name": "示例主力机场 (含拦截规则)",
        "targetVersion": "1.14",
        "enableTun": True,
        "rejectRules": {
            "domains": ["tiktok.com", "douyin.com", "adservice.google.com"],
            "ips": ["123.56.78.90/32"],
            "packages": ["com.ss.android.ugc.aweme", "pinduoduo.exe"]
        },
        "updatedAt": "2026-09-12T06:30:00.000Z"
    })
}

with open(r"z:\SingBoxConverert\src\index.js", "r", encoding="utf-8") as f:
    js_content = f.read()

start_marker = "function renderHtml(origin) {"
end_marker = "</html>`;"
idx1 = js_content.find(start_marker)
idx2 = js_content.find(end_marker, idx1)
html_template = js_content[idx1 + len(start_marker):idx2 + 7].strip()
if html_template.startswith("return `"):
    html_template = html_template[8:]

class LocalDevHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_template.encode("utf-8"))
        elif self.path == "/api/list":
            items = []
            for k, v in mock_kv.items():
                if k.startswith("sub:"):
                    obj = json.loads(v)
                    items.append({"id": k.replace("sub:", ""), **obj})
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"items": items}).encode("utf-8"))
        elif self.path.startswith("/sub/"):
            sub_id = self.path[5:]
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            raw_entry = mock_kv.get(f"sub:{sub_id}")
            rules = json.loads(raw_entry).get("rejectRules", {}) if raw_entry else {}
            demo_resp = {
                "message": f"客户端访问 /sub/{sub_id}，由 Worker 实时转换返回 Sing-box 1.14+ JSON",
                "dns": {
                    "servers": [{"tag": "dns-fakeip", "type": "fakeip"}],
                    "rules": [
                        {"action": "reject", "domain": rules.get("domains", [])}
                    ]
                },
                "route": {
                    "rules": [
                        {"action": "sniff"},
                        {"action": "hijack-dns"},
                        {"action": "reject", "domain": rules.get("domains", [])},
                        {"action": "reject", "ip_cidr": rules.get("ips", [])},
                        {"action": "reject", "package_name": rules.get("packages", [])}
                    ]
                }
            }
            self.wfile.write(json.dumps(demo_resp, indent=2, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
        
        if self.path == "/api/create":
            sub_id = body.get("id") or "sub_" + os.urandom(3).hex()
            mock_kv[f"sub:{sub_id}"] = json.dumps({
                "sourceUrl": body.get("sourceUrl"),
                "name": body.get("name") or "未命名订阅",
                "targetVersion": body.get("targetVersion", "1.14"),
                "enableTun": body.get("enableTun", True),
                "rejectRules": {
                    "domains": [s.strip() for s in body.get("rejectDomains", "").replace("\n", ",").split(",") if s.strip()],
                    "ips": [s.strip() for s in body.get("rejectIps", "").replace("\n", ",").split(",") if s.strip()],
                    "packages": [s.strip() for s in body.get("rejectPackages", "").replace("\n", ",").split(",") if s.strip()]
                },
                "updatedAt": "2026-09-12T06:30:00.000Z"
            })
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "id": sub_id}).encode("utf-8"))
        elif self.path == "/api/delete":
            sub_id = body.get("id")
            if f"sub:{sub_id}" in mock_kv:
                del mock_kv[f"sub:{sub_id}"]
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

print(f"Local Worker Server started at http://127.0.0.1:{PORT}")
with socketserver.TCPServer(("127.0.0.1", PORT), LocalDevHandler) as httpd:
    httpd.serve_forever()
