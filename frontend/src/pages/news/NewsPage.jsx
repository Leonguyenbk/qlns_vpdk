import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import NewsTabBar from "../../components/NewsTabBar";
import { PageHeader } from "../../components/ui/primitives";
import { useNews } from "../../components/newsContext";

const PAGE_SIZE = 9;

function formatDate(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return d.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function Pagination({ page, total, pageSize, onChange }) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  return (
    <div className="mt-8 flex items-center justify-center gap-2">
      <button
        onClick={() => onChange(page - 1)}
        disabled={page === 1}
        className="rounded-lg border border-rule bg-paper px-3 py-1.5 text-sm text-ink-2 transition-colors hover:bg-[#f1f5f9] disabled:cursor-not-allowed disabled:opacity-40"
      >
        ← Trước
      </button>

      {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
        <button
          key={p}
          onClick={() => onChange(p)}
          className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
            p === page
              ? "border-[color:var(--color-accent)] bg-[var(--color-accent)] text-white"
              : "border-rule bg-paper text-ink-2 hover:bg-[#f1f5f9]"
          }`}
        >
          {p}
        </button>
      ))}

      <button
        onClick={() => onChange(page + 1)}
        disabled={page === totalPages}
        className="rounded-lg border border-rule bg-paper px-3 py-1.5 text-sm text-ink-2 transition-colors hover:bg-[#f1f5f9] disabled:cursor-not-allowed disabled:opacity-40"
      >
        Sau →
      </button>
    </div>
  );
}

export default function NewsPage() {
  const [allNews, setAllNews] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();
  const { setNewCount } = useNews();

  useEffect(() => {
    const fetchNews = () => {
      fetch("/news.json")
        .then((r) => {
          if (!r.ok) throw new Error("Không tải được dữ liệu");
          return r.json();
        })
        .then((data) => {
          const filtered = data
            .filter((item) => item.category === "tin-tuc")
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

          setAllNews((prev) => {
            const prevIds = new Set(prev.map((item) => item.id));
            const newItems = filtered.filter((item) => !prevIds.has(item.id));
            if (newItems.length > 0 && prev.length > 0) {
              setNewCount(newItems.length);
            }
            return newItems.length > 0 ? filtered : prev;
          });
          setIsLoading(false);
        })
        .catch((err) => {
          console.error("Lỗi fetch news:", err.message);
          setIsError(true);
          setIsLoading(false);
        });
    };

    fetchNews(); // Chạy ngay lần đầu

    // Polling mỗi 3 tiếng
    const interval = setInterval(fetchNews, 3 * 60 * 60 * 1000);

    return () => clearInterval(interval); // Cleanup khi unmount
  }, []);

  const total = allNews.length;
  const paged = allNews.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div>
      <PageHeader
        eyebrow="Sở Tài nguyên và Môi trường Đắk Lắk"
        title="Tổng quan"
        subtitle="Tin tức, thông báo về đất đai tỉnh Đắk Lắk"
      />

      <NewsTabBar />

      {isLoading ? (
        <p className="py-12 text-center text-sm text-muted">
          Đang tải dữ liệu…
        </p>
      ) : isError ? (
        <p className="py-12 text-center text-sm text-danger">
          Không tải được dữ liệu. Vui lòng thử lại.
        </p>
      ) : paged.length === 0 ? (
        <p className="py-12 text-center text-sm text-muted">
          Không tìm thấy dữ liệu.
        </p>
      ) : (
        <>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {paged.map((item) => (
              <div
                key={item.id}
                onClick={() => navigate(`/tin-tuc/${item.slug}`)}
                className="card group flex cursor-pointer flex-col overflow-hidden transition-shadow hover:shadow-md"
              >
                {/* Thumbnail */}
                <div className="h-44 w-full shrink-0 overflow-hidden bg-[#f1f5f9]">
                  {item.image ? (
                    <img
                      src={item.image}
                      alt={item.title}
                      className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      loading="lazy"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-[#cbd5e1]">
                      <svg
                        width="48"
                        height="48"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                      >
                        <rect x="3" y="3" width="18" height="18" rx="2" />
                        <circle cx="8.5" cy="8.5" r="1.5" />
                        <path d="M21 15l-5-5L5 21" />
                      </svg>
                    </div>
                  )}
                </div>

                {/* Nội dung card */}
                <div className="flex flex-1 flex-col gap-2 p-5">
                  <h2 className="line-clamp-2 font-semibold leading-snug text-ink group-hover:text-accent-text">
                    {item.title}
                  </h2>
                  <p className="line-clamp-3 flex-1 text-sm leading-6 text-ink-2">
                    {item.summary}
                  </p>
                  <span className="mt-auto text-xs text-muted">
                    {formatDate(item.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <Pagination
            page={page}
            total={total}
            pageSize={PAGE_SIZE}
            onChange={setPage}
          />
        </>
      )}
    </div>
  );
}
