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

  images: {
    // Loyihada `next/image` ishlatilmaydi. Bu bayroqsiz Next standalone
    // build'ga `sharp` ning **build qilingan platformasi uchun** native
    // binarisini qo'shadi — Windows'da build qilib Linuxga tashiganda u
    // ishlamaydi. Optimizatsiya o'chirilgach sharp umuman kerak emas.
    unoptimized: true,
  },
  // sharp'ni tracing'dan ham chiqaramiz — standalone 60 MB dan ~15 MB ga tushadi.
  outputFileTracingExcludes: {
    "*": ["node_modules/@img/**", "node_modules/sharp/**"],
  },

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
