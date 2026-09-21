import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PageHeader } from "../../components/ui/primitives";

function formatDate(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return d.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** Phát hiện chuỗi là HTML hay plain text */
function isHtml(str) {
  return /<[a-z][\s\S]*>/i.test(str);
}

/** Loại bỏ các thẻ h1, heading, ngày cập nhật trùng lặp có sẵn trong HTML được cào */
function cleanArticleContent(html, title) {
  if (!html) return "";
  let cleaned = html;
  // Bỏ thẻ h1 (tiêu đề đã hiển thị ở phần trên của trang)
  cleaned = cleaned.replace(/<h1[^>]*>[\s\S]*?<\/h1>/gi, "");
  // Bỏ khối hiển thị ngày/cập nhật lúc bị cào lẫn
  cleaned = cleaned.replace(
    /<p[^>]*id=["']publishupshow-bottom["'][^>]*>[\s\S]*?<\/p>/gi,
    "",
  );
  // Bỏ các đoạn tiêu đề lặp lại nếu có
  return cleaned.trim();
}

export default function NewsDetailPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    fetch("/news.json")
      .then((r) => {
        if (!r.ok) throw new Error("Không tải được dữ liệu");
        return r.json();
      })
      .then((data) => {
        const found = data.find((n) => n.slug === slug);
        setItem(found || null);
        setIsLoading(false);
      })
      .catch(() => {
        setIsError(true);
        setIsLoading(false);
      });
  }, [slug]);

  if (isLoading) {
    return (
      <div className="py-12 text-center text-sm text-muted">
        Đang tải bài viết…
      </div>
    );
  }

  if (isError) {
    return (
      <div className="py-12 text-center text-sm text-danger">
        Không tải được dữ liệu. Vui lòng thử lại.
      </div>
    );
  }

  if (!item) {
    return (
      <div className="py-12 text-center">
        <p className="text-sm text-muted">Không tìm thấy bài viết.</p>
        <button
          onClick={() => navigate("/tin-tuc")}
          className="mt-4 text-sm text-accent-text underline hover:opacity-80"
        >
          ← Quay lại danh sách
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      {/* Breadcrumb */}
      <nav className="mb-6 flex flex-wrap items-center gap-1.5 text-sm text-muted">
        <Link to="/" className="hover:text-accent-text">
          Tổng quan
        </Link>
        <span>/</span>
        <Link to="/tin-tuc" className="hover:text-accent-text">
          Tin tức
        </Link>
        <span>/</span>
        <span className="truncate font-medium text-ink">{item.title}</span>
      </nav>

      {/* Nút quay lại */}
      <button
        onClick={() => navigate("/tin-tuc")}
        className="mb-6 inline-flex items-center gap-1.5 rounded-lg border border-rule bg-paper px-3 py-1.5 text-sm text-ink-2 transition-colors hover:bg-[#f1f5f9] hover:text-accent-text"
      >
        ← Quay lại
      </button>

      {/* Tiêu đề */}
      <h1 className="font-display text-2xl font-bold leading-tight text-ink sm:text-3xl">
        {item.title}
      </h1>

      {/* Ngày đăng */}
      <p className="mt-3 text-sm text-muted">
        Ngày đăng: {formatDate(item.created_at)}
      </p>

      <hr className="my-6 border-rule" />

      {/* Nội dung */}
      <div className="card p-6">
        {isHtml(item.content) ? (
          <div
            className="prose prose-sm max-w-none text-ink-2"
            dangerouslySetInnerHTML={{
              __html: cleanArticleContent(item.content, item.title),
            }}
          />
        ) : (
          <p className="whitespace-pre-wrap text-sm leading-7 text-ink-2">
            {item.content}
          </p>
        )}
      </div>
    </div>
  );
}
