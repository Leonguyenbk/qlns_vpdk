import { useMemo } from "react";

/** Tọa độ gần đúng: 46 Phan Bội Châu, Buôn Ma Thuột, Đắk Lắk */
const OFFICE = {
  lat: 12.6667,
  lng: 108.038,
  query: "46 Phan Bội Châu, Phường Buôn Ma Thuột, Tỉnh Đắk Lắk",
};

/**
 * Bản đồ Google — dùng Embed API nếu có VITE_GOOGLE_MAPS_API_KEY,
 * không thì fallback query embed (không cần key).
 */
function FooterMap({ className = "" }) {
  const src = useMemo(() => {
    const key = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
    if (key) {
      const params = new URLSearchParams({
        key,
        q: OFFICE.query,
        zoom: "16",
        language: "vi",
      });
      return `https://www.google.com/maps/embed/v1/place?${params.toString()}`;
    }
    const q = encodeURIComponent(OFFICE.query);
    return `https://maps.google.com/maps?q=${q}&z=16&hl=vi&output=embed`;
  }, []);

  return (
    <div
      className={[
        "overflow-hidden rounded-md border border-[#2e4a62]/0.5px] bg-[#0d2137] shadow-sm",
        className,
      ].join(" ")}
    >
      <iframe
        title="Bản đồ — Văn phòng đăng ký đất đai tỉnh Đắk Lắk"
        src={src}
        className="h-full w-full border-0"
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
        allowFullScreen
      />
    </div>
  );
}

export default function Footer() {
  const contacts = [
    { icon: "📍", text: "Địa chỉ: 46 Phan Bội Châu, Phường Buôn Ma Thuột, Tỉnh Đắk Lắk" },
    { icon: "📞", text: "Số điện thoại: 012345789" },
    { icon: "✉️", text: "Email: admin@gmail.com" },
  ];

  return (
    <footer className="bg-[#003366] text-white border-t-4 border-[#ffcc00] px-4 pb-4 pt-6 sm:px-6 sm:pb-5 sm:pt-7 md:px-8 md:pb-5 md:pt-8">
      {/* Top: thông tin trái — bản đồ phải */}
      <div className="grid gap-6 lg:grid-cols-2 lg:items-start lg:gap-8">
        <div className="min-w-0">
          <h2 className="mb-4 text-base font-medium leading-snug text-[#f0c060] sm:mb-5 sm:text-lg md:text-xl">
            VĂN PHÒNG ĐĂNG KÝ ĐẤT ĐAI TỈNH ĐẮK LẮK
          </h2>

          <div className="space-y-3 text-sm">
            {contacts.map((row) => (
              <div key={row.text} className="flex items-start gap-2.5">
                <span className="shrink-0 leading-5" aria-hidden="true">
                  {row.icon}
                </span>
                <span className="min-w-0 break-words leading-5">{row.text}</span>
              </div>
            ))}

            <div className="flex items-start gap-2.5">
              <span className="shrink-0 leading-5" aria-hidden="true">
                🕐
              </span>
              <div className="min-w-0 leading-5">
                <div>Giờ làm việc: Thứ 2 – Thứ 6</div>
                <div className="mt-1 flex flex-col gap-0.5 text-[#7a9ab8] sm:flex-row sm:flex-wrap sm:items-center sm:gap-x-2">
                  <span>Sáng: 7:30 – 11:30</span>
                  <span className="hidden text-[#2e4a62] sm:inline" aria-hidden="true">
                    |
                  </span>
                  <span>Chiều: 13:30 – 17:00</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <FooterMap className="h-[220px] w-full sm:h-[260px] lg:h-[280px]" />
      </div>

      {/* Footer bottom — 3 cột */}
      <div className="bg-[#002244] border-t border-[#1a4a7a] -mx-4 mt-6 text-center text-[#cce0ff] px-4 py-5 text-[12px] leading-relaxed sm:-mx-6 sm:px-6 md:-mx-8 md:px-8 md:py-6">
        <div className="flex justify-center items-center">
          <p>© 2026 Ủy ban nhân dân phường Buôn Ma Thuột.</p>
        </div>
      </div>
    </footer>
  );
}
