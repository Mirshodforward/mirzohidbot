import path from "node:path";
import type { NextConfig } from "next";

const API_ORIGIN = process.env.API_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Standalone build — Docker image kichik bo'ladi (node_modules ko'chirilmaydi).
  output: "standalone",
  // Ildizni aniq ko'rsatamiz: aks holda Next yuqoridagi begona lockfile'ni
  // topib, standalone build'ga noto'g'ri fayllarni yig'adi.
  outputFileTracingRoot: path.join(__dirname),

  async rewrites() {
    // Brauzer /api/... ga uradi, Next uni FastAPI ga uzatadi. Shu tufayli
    // frontend va backend bitta origin: CORS va cookie muammosi yo'q.
    return [{ source: "/api/:path*", destination: `${API_ORIGIN}/api/:path*` }];
  },

  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          // Telegram Mini App sahifani iframe ichida ochadi — shuning uchun
          // X-Frame-Options: DENY QO'YMANG, mini app oq ekran bo'lib qoladi.
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
