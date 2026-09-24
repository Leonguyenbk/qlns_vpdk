import { useState, useMemo, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import toast from "react-hot-toast";
import { usePublicSurveyResults } from "../../hooks/usePublicSurvey";
import { apiErrorMessage } from "../../lib/api";

// --- SVG Icons (Lucide-style stroke voice) ---
function IconTrophy({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
      <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
      <path d="M4 22h16" />
      <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
      <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
      <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
    </svg>
  );
}

function IconMedal({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M7.21 15 2.66 7.14a2 2 0 0 1 .13-2.2L4.4 2.8A2 2 0 0 1 6 2h12a2 2 0 0 1 1.6.8l1.6 2.14a2 2 0 0 1 .14 2.2L16.79 15" />
      <path d="M11 12 5.12 2.2" />
      <path d="m13 12 5.88-9.8" />
      <circle cx="12" cy="17" r="5" />
    </svg>
  );
}

function IconSparkles({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" />
    </svg>
  );
}

function IconBuilding({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <rect width="16" height="20" x="4" y="2" rx="2" ry="2" />
      <path d="M9 22v-4h6v4" />
      <path d="M8 6h.01" />
      <path d="M16 6h.01" />
      <path d="M12 6h.01" />
      <path d="M12 10h.01" />
      <path d="M12 14h.01" />
      <path d="M16 10h.01" />
      <path d="M16 14h.01" />
      <path d="M8 10h.01" />
      <path d="M8 14h.01" />
    </svg>
  );
}

function IconUsers({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function IconGauge({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="m12 14 4-4" />
      <path d="M3.34 19a10 10 0 1 1 17.32 0" />
    </svg>
  );
}

function IconRefresh({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M21 12a9 9 0 1 1-3-6.7L21 8" />
      <path d="M21 3v5h-5" />
    </svg>
  );
}

function IconShare({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
      <polyline points="16 6 12 2 8 6" />
      <line x1="12" y1="2" x2="12" y2="15" />
    </svg>
  );
}

function IconSearch({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

function IconArrowRight({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </svg>
  );
}

function IconLock({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

function IconShieldCheck({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

function IconAlert({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <circle cx="12" cy="12" r="10" />
      <line x1="12" x2="12" y1="8" y2="12" />
      <line x1="12" x2="12.01" y1="16" y2="16" />
    </svg>
  );
}

function IconChartBar({ className = "w-5 h-5", ...props }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M3 3v18h18" />
      <path d="M18 17V9" />
      <path d="M13 17V5" />
      <path d="M8 17v-3" />
    </svg>
  );
}

// --- Skeleton Placeholder ---
function LeaderboardSkeleton() {
  return (
    <div className="min-h-screen bg-canvas px-4 py-8 sm:py-12">
      <div className="mx-auto w-full max-w-5xl space-y-8 animate-pulse">
        {/* Header Skeleton */}
        <div className="rounded-2xl border border-rule bg-paper p-6 sm:p-8">
          <div className="mx-auto h-4 w-48 rounded bg-slate-200" />
          <div className="mx-auto mt-3 h-8 w-3/4 max-w-md rounded-lg bg-slate-200" />
          <div className="mx-auto mt-3 h-4 w-1/2 max-w-sm rounded bg-slate-200" />
        </div>

        {/* KPI Skeleton */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 rounded-2xl border border-rule bg-paper p-4">
              <div className="h-4 w-20 rounded bg-slate-200" />
              <div className="mt-3 h-7 w-28 rounded bg-slate-200" />
              <div className="mt-2 h-3 w-16 rounded bg-slate-200" />
            </div>
          ))}
        </div>

        {/* Podium Skeleton */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 rounded-2xl border border-rule bg-paper p-6" />
          ))}
        </div>

        {/* Table Skeleton */}
        <div className="rounded-2xl border border-rule bg-paper p-6">
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-14 rounded-xl bg-slate-100" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Shell Component for Consistent Look ---
function PublicShell({ children }) {
  return (
    <div className="min-h-screen bg-canvas selection:bg-brand-500 selection:text-white">
      {/* Subtle Ambient Background Glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[900px] h-[450px] bg-gradient-to-b from-indigo-100/60 via-purple-50/30 to-transparent blur-3xl opacity-70" />
      </div>

      <div className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 sm:py-10">
        {children}
      </div>
    </div>
  );
}

// --- Rank Medal Component ---
function RankBadge({ rank, size = "md" }) {
  const isLarge = size === "lg";
  const baseDim = isLarge ? "w-12 h-12 text-base" : "w-9 h-9 text-sm";

  if (rank === 1) {
    return (
      <div
        className={`relative flex ${baseDim} shrink-0 items-center justify-center rounded-xl font-bold shadow-md bg-gradient-to-br from-amber-300 via-amber-400 to-yellow-500 text-amber-950 ring-2 ring-amber-200/90`}
        title="Quán quân - Hạng 1"
      >
        <IconTrophy className={isLarge ? "w-6 h-6 drop-shadow-sm" : "w-4 h-4"} />
      </div>
    );
  }

  if (rank === 2) {
    return (
      <div
        className={`relative flex ${baseDim} shrink-0 items-center justify-center rounded-xl font-bold shadow-sm bg-gradient-to-br from-slate-200 via-slate-300 to-slate-400 text-slate-800 ring-2 ring-slate-200`}
        title="Á quân - Hạng 2"
      >
        <IconMedal className={isLarge ? "w-6 h-6" : "w-4 h-4"} />
      </div>
    );
  }

  if (rank === 3) {
    return (
      <div
        className={`relative flex ${baseDim} shrink-0 items-center justify-center rounded-xl font-bold shadow-sm bg-gradient-to-br from-amber-600 via-orange-600 to-amber-700 text-white ring-2 ring-orange-200`}
        title="Hạng 3"
      >
        <IconMedal className={isLarge ? "w-6 h-6" : "w-4 h-4"} />
      </div>
    );
  }

  return (
    <div
      className={`flex ${baseDim} shrink-0 items-center justify-center rounded-xl font-mono font-semibold bg-paper-3 text-ink-2 border border-rule`}
    >
      #{rank || "—"}
    </div>
  );
}

// --- Podium Card Component ---
function PodiumCard({ branch, position, maxScore }) {
  const isFirst = position === 1;
  const isSecond = position === 2;
  const isThird = position === 3;

  const cardStyling = isFirst
    ? "border-amber-300/80 bg-gradient-to-b from-amber-500/10 via-amber-50/40 to-paper shadow-lg shadow-amber-500/10 ring-1 ring-amber-400/40 order-1 md:order-2 md:-translate-y-3"
    : isSecond
    ? "border-slate-300 bg-gradient-to-b from-slate-200/40 via-slate-50/40 to-paper shadow-sm order-2 md:order-1"
    : "border-orange-200 bg-gradient-to-b from-orange-100/40 via-orange-50/20 to-paper shadow-sm order-3";

  const titleBadge = isFirst
    ? { text: "QUÁN QUÂN", bg: "bg-amber-100 text-amber-900 border-amber-300" }
    : isSecond
    ? { text: "Á QUÂN", bg: "bg-slate-100 text-slate-800 border-slate-300" }
    : { text: "HẠNG BA", bg: "bg-orange-100 text-orange-900 border-orange-200" };

  return (
    <div className={`relative flex flex-col justify-between rounded-2xl border p-5 sm:p-6 transition-all duration-200 hover:shadow-md ${cardStyling}`}>
      {/* Decorative Crown/Ribbon for 1st Place */}
      {isFirst && (
        <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 flex items-center gap-1.5 rounded-full bg-gradient-to-r from-amber-500 to-yellow-500 px-3 py-0.5 text-xs font-semibold text-white shadow-sm ring-2 ring-white">
          <IconSparkles className="w-3.5 h-3.5" />
          <span>Dẫn Đầu Hệ Thống</span>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between gap-2">
          <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider ${titleBadge.bg}`}>
            {titleBadge.text}
          </span>
          <RankBadge rank={branch.rank} size="md" />
        </div>

        <h3 className="mt-4 font-display text-base sm:text-lg font-bold text-ink line-clamp-2" title={branch.branch_name}>
          {branch.branch_name}
        </h3>

        <p className="mt-1 text-xs text-muted flex items-center gap-1.5">
          <IconUsers className="w-3.5 h-3.5 text-muted" />
          <span>{branch.total_responses} lượt đánh giá</span>
        </p>
      </div>

      <div className="mt-6 pt-4 border-t border-rule/60">
        <div className="flex items-baseline justify-between">
          <div>
            <span className="text-2xl sm:text-3xl font-bold tracking-tight text-ink font-mono">
              {branch.average_total_score}
            </span>
            {maxScore ? (
              <span className="ml-1 text-xs text-muted font-mono">/{maxScore} đ</span>
            ) : (
              <span className="ml-1 text-xs text-muted">điểm</span>
            )}
          </div>
          {branch.average_percentage !== null && (
            <span className="inline-flex items-center rounded-lg bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700 border border-emerald-200">
              {branch.average_percentage}%
            </span>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isFirst
                ? "bg-gradient-to-r from-amber-400 to-yellow-500"
                : isSecond
                ? "bg-gradient-to-r from-slate-400 to-slate-500"
                : "bg-gradient-to-r from-orange-400 to-amber-600"
            }`}
            style={{ width: `${Math.min(100, Math.max(0, branch.average_percentage ?? 0))}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// --- Main Page Component ---
export default function PublicSurveyResultsPage() {
  const { slug } = useParams();
  const { data, isLoading, isError, error, refetch, isFetching } = usePublicSurveyResults(slug);

  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("rank"); // "rank" | "score_desc" | "responses_desc" | "name_asc"

  // Handle Share / Copy Link
  const handleShare = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success("Đã sao chép liên kết bảng xếp hạng!");
    } catch {
      toast.error("Không thể tự động sao chép, vui lòng copy đường dẫn trên thanh địa chỉ.");
    }
  }, []);

  // System Stats
  const stats = useMemo(() => {
    if (!data?.by_branch?.length) {
      return { totalBranches: 0, avgSatisfaction: null, topBranch: null };
    }
    const totalBranches = data.by_branch.length;
    const topBranch = data.by_branch.find((b) => b.rank === 1) || data.by_branch[0];

    const validPercents = data.by_branch
      .map((b) => b.average_percentage)
      .filter((p) => p !== null && !isNaN(p));

    const avgSatisfaction = validPercents.length
      ? Math.round((validPercents.reduce((a, b) => a + b, 0) / validPercents.length) * 10) / 10
      : null;

    return { totalBranches, avgSatisfaction, topBranch };
  }, [data?.by_branch]);

  // Top 3 for Podium
  const topThree = useMemo(() => {
    if (!data?.by_branch || data.by_branch.length < 2) return [];
    return [...data.by_branch]
      .sort((a, b) => (a.rank || 999) - (b.rank || 999))
      .slice(0, 3);
  }, [data?.by_branch]);

  // Processed branch list for Leaderboard
  const processedBranches = useMemo(() => {
    if (!data?.by_branch) return [];
    let list = [...data.by_branch];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter((b) => b.branch_name.toLowerCase().includes(q));
    }

    if (sortBy === "score_desc") {
      list.sort((a, b) => (b.average_total_score || 0) - (a.average_total_score || 0));
    } else if (sortBy === "responses_desc") {
      list.sort((a, b) => (b.total_responses || 0) - (a.total_responses || 0));
    } else if (sortBy === "name_asc") {
      list.sort((a, b) => a.branch_name.localeCompare(b.branch_name, "vi"));
    } else {
      list.sort((a, b) => (a.rank || 999) - (b.rank || 999));
    }

    return list;
  }, [data?.by_branch, searchQuery, sortBy]);

  // 1. Loading State
  if (isLoading) {
    return <LeaderboardSkeleton />;
  }

  // 2. Error State
  if (isError || !data) {
    return (
      <PublicShell>
        <div className="mx-auto max-w-md py-16 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-50 text-rose-600 ring-8 ring-rose-50/50">
            <IconAlert className="w-7 h-7" />
          </div>
          <h2 className="mt-5 font-display text-xl font-bold text-ink">
            Không thể tải bảng xếp hạng
          </h2>
          <p className="mt-2 text-sm text-ink-2">
            {apiErrorMessage(error, "Không tìm thấy khảo sát hoặc kết quả không khả dụng.")}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <button
              onClick={() => refetch()}
              className="btn btn-primary inline-flex items-center gap-2"
            >
              <IconRefresh className="w-4 h-4" />
              Thử lại
            </button>
          </div>
        </div>
      </PublicShell>
    );
  }

  // 3. Not Available State
  if (!data.available) {
    return (
      <PublicShell>
        <div className="mx-auto max-w-lg py-12 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-indigo-50 text-brand-600 ring-8 ring-indigo-50/50">
            <IconLock className="w-8 h-8" />
          </div>
          <p className="eyebrow mt-5 text-brand-600">Thông báo công khai</p>
          <h2 className="mt-2 font-display text-2xl font-bold text-ink tracking-tight">
            {data.title || "Khảo sát ý kiến người dân"}
          </h2>
          <div className="mt-4 rounded-xl border border-rule bg-paper p-5 text-sm text-ink-2 shadow-sm">
            <p className="font-medium text-ink">
              {data.unavailable_reason || "Khảo sát này hiện chưa công khai bảng xếp hạng kết quả."}
            </p>
            <p className="mt-2 text-xs text-muted leading-relaxed">
              Bảng xếp hạng sẽ được tự động hiển thị sau khi ban tổ chức tiến hành công bố số liệu
              chính thức. Quý khách vẫn có thể tham gia đóng góp ý kiến đánh giá để giúp đơn vị nâng cao chất lượng phục vụ.
            </p>
          </div>

          <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to={`/khao-sat/${slug}`}
              className="btn btn-primary w-full sm:w-auto inline-flex items-center justify-center gap-2"
            >
              <span>Tham gia làm khảo sát</span>
              <IconArrowRight className="w-4 h-4" />
            </Link>
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="btn btn-secondary w-full sm:w-auto inline-flex items-center justify-center gap-2"
            >
              <IconRefresh className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`} />
              <span>Kiểm tra lại</span>
            </button>
          </div>
        </div>
      </PublicShell>
    );
  }

  // 4. Success State (Available & Loaded)
  return (
    <PublicShell>
      {/* Top Header & Brand Bar */}
      <header className="relative overflow-hidden rounded-3xl border border-rule bg-paper p-6 sm:p-8 shadow-card">
        {/* Subtle decorative gradient top bar */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600" />

        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                Dữ liệu trực tiếp
              </span>
              <span className="eyebrow text-muted">VĂN PHÒNG ĐĂNG KÝ ĐẤT ĐAI</span>
            </div>

            <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-ink">
              {data.title}
            </h1>

            <p className="text-sm text-ink-2 max-w-2xl leading-relaxed">
              Bảng xếp hạng mức độ hài lòng và đánh giá chất lượng phục vụ của các chi nhánh trực thuộc,
              dựa trên kết quả khảo sát minh bạch từ người dân và doanh nghiệp.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5 sm:self-start shrink-0">
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              title="Cập nhật kết quả mới nhất"
              className="btn btn-secondary inline-flex items-center gap-2 text-xs"
            >
              <IconRefresh className={`w-4 h-4 ${isFetching ? "animate-spin text-brand-600" : ""}`} />
              <span className="hidden sm:inline">Làm mới</span>
            </button>

            <button
              onClick={handleShare}
              title="Sao chép đường dẫn chia sẻ bảng xếp hạng"
              className="btn btn-secondary inline-flex items-center gap-2 text-xs"
            >
              <IconShare className="w-4 h-4" />
              <span>Chia sẻ</span>
            </button>

            <Link
              to={`/khao-sat/${slug}`}
              className="btn btn-primary inline-flex items-center gap-2 text-xs shadow-sm"
              title="Đi tới trang làm bài khảo sát"
            >
              <span>Đánh giá ngay</span>
              <IconArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* KPI Overview Summary Cards */}
      <section className="mt-6 grid grid-cols-2 gap-3.5 sm:gap-4 lg:grid-cols-4" aria-label="Tổng quan khảo sát">
        {/* KPI 1: Total Responses */}
        <div className="rounded-2xl border border-rule bg-paper p-4 sm:p-5 shadow-card transition-all hover:border-indigo-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted">Tổng lượt đánh giá</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-50 text-brand-600">
              <IconUsers className="w-4 h-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-ink font-mono">
            {data.total_responses.toLocaleString("vi-VN")}
          </p>
          <p className="mt-1 text-xs text-muted">Phiếu phản hồi hợp lệ</p>
        </div>

        {/* KPI 2: Evaluated Branches */}
        <div className="rounded-2xl border border-rule bg-paper p-4 sm:p-5 shadow-card transition-all hover:border-indigo-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted">Chi nhánh tham gia</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
              <IconBuilding className="w-4 h-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-ink font-mono">
            {stats.totalBranches}
          </p>
          <p className="mt-1 text-xs text-muted">Đơn vị được xếp hạng</p>
        </div>

        {/* KPI 3: System Satisfaction / Scale */}
        <div className="rounded-2xl border border-rule bg-paper p-4 sm:p-5 shadow-card transition-all hover:border-indigo-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted">Điểm chuẩn khảo sát</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
              <IconGauge className="w-4 h-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-ink font-mono">
            {data.max_possible_score ? `${data.max_possible_score} đ` : "100%"}
          </p>
          <p className="mt-1 text-xs text-muted">
            {stats.avgSatisfaction !== null ? `Đạt TB ~${stats.avgSatisfaction}%` : "Thang điểm chuẩn hóa"}
          </p>
        </div>

        {/* KPI 4: Top Performer */}
        <div className="rounded-2xl border border-rule bg-paper p-4 sm:p-5 shadow-card transition-all hover:border-amber-300">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted">Đơn vị dẫn đầu</span>
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
              <IconTrophy className="w-4 h-4" />
            </div>
          </div>
          <p className="mt-2 text-base sm:text-lg font-bold text-ink truncate" title={stats.topBranch?.branch_name}>
            {stats.topBranch?.branch_name || "—"}
          </p>
          <p className="mt-1 text-xs text-amber-700 font-medium">
            {stats.topBranch
              ? `${stats.topBranch.average_total_score} điểm (${stats.topBranch.average_percentage || 0}%)`
              : "Chưa có dữ liệu"}
          </p>
        </div>
      </section>

      {/* Top 3 Podium Showcase (Displayed if 2 or more branches exist) */}
      {topThree.length >= 2 && (
        <section className="mt-8">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="font-display text-lg font-bold text-ink">Bục Vinh Danh Top Dẫn Đầu</h2>
              <p className="text-xs text-muted">Các chi nhánh có điểm số đánh giá xuất sắc nhất</p>
            </div>
            <span className="hidden sm:inline-flex items-center gap-1 text-xs font-medium text-amber-600">
              <IconSparkles className="w-3.5 h-3.5" />
              <span>Thành tích tiêu biểu</span>
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:items-end">
            {/* If 3 branches: show in Olympic order (Rank 2 left, Rank 1 center, Rank 3 right) */}
            {topThree.length === 3 ? (
              <>
                <PodiumCard branch={topThree[1]} position={2} maxScore={data.max_possible_score} />
                <PodiumCard branch={topThree[0]} position={1} maxScore={data.max_possible_score} />
                <PodiumCard branch={topThree[2]} position={3} maxScore={data.max_possible_score} />
              </>
            ) : (
              // If only 2 branches
              <>
                <PodiumCard branch={topThree[0]} position={1} maxScore={data.max_possible_score} />
                <PodiumCard branch={topThree[1]} position={2} maxScore={data.max_possible_score} />
              </>
            )}
          </div>
        </section>
      )}

      {/* Detailed Leaderboard Section */}
      <section className="mt-8 rounded-3xl border border-rule bg-paper p-5 sm:p-7 shadow-card">
        {/* Table Toolbar: Title, Search & Filter */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-5 border-b border-rule">
          <div>
            <h2 className="font-display text-lg font-bold text-ink">Bảng Xếp Hạng Chi Nhánh</h2>
            <p className="text-xs text-muted">
              Hiển thị {processedBranches.length}/{data.by_branch.length} chi nhánh được đánh giá
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search Input */}
            <div className="relative min-w-[200px] flex-1 sm:w-64">
              <IconSearch className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm tên chi nhánh…"
                className="input pl-9 pr-3 text-xs w-full"
              />
            </div>

            {/* Sort Select */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="input text-xs w-auto py-1 px-3"
            >
              <option value="rank">Thứ hạng (Cao → Thấp)</option>
              <option value="score_desc">Điểm TB (Cao nhất)</option>
              <option value="responses_desc">Nhiều lượt đánh giá nhất</option>
              <option value="name_asc">Tên chi nhánh (A → Z)</option>
            </select>
          </div>
        </div>

        {/* Leaderboard Content */}
        {data.by_branch.length === 0 ? (
          <div className="py-12 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-paper-3 text-muted">
              <IconChartBar className="w-6 h-6" />
            </div>
            <p className="mt-3 text-sm font-medium text-ink">Chưa có dữ liệu xếp hạng</p>
            <p className="mt-1 text-xs text-muted">
              Hệ thống chưa ghi nhận lượt đánh giá hợp lệ nào cho các chi nhánh thuộc khảo sát này.
            </p>
          </div>
        ) : processedBranches.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm font-medium text-ink">Không tìm thấy chi nhánh phù hợp</p>
            <p className="mt-1 text-xs text-muted">
              Không có kết quả nào khớp với từ khóa &ldquo;{searchQuery}&rdquo;.
            </p>
            <button
              onClick={() => setSearchQuery("")}
              className="btn btn-secondary mt-3 text-xs"
            >
              Xóa bộ lọc tìm kiếm
            </button>
          </div>
        ) : (
          <div className="mt-4 divide-y divide-rule/60">
            {processedBranches.map((row) => {
              const isLead = row.rank === 1;
              const percent = row.average_percentage ?? 0;

              return (
                <div
                  key={row.branch_id}
                  className={`flex flex-col gap-3 py-3.5 sm:flex-row sm:items-center sm:justify-between sm:gap-4 rounded-xl px-3 transition-colors hover:bg-paper-2 ${
                    isLead ? "bg-amber-500/[0.03]" : ""
                  }`}
                >
                  {/* Left: Rank & Branch Name */}
                  <div className="flex items-center gap-3.5 min-w-0 flex-1">
                    <RankBadge rank={row.rank} size="md" />

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-ink text-sm sm:text-base truncate" title={row.branch_name}>
                          {row.branch_name}
                        </span>
                        {isLead && (
                          <span className="hidden sm:inline-flex items-center gap-1 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-800">
                            ★ Top 1
                          </span>
                        )}
                      </div>
                      <p className="mt-0.5 text-xs text-muted flex items-center gap-1.5">
                        <span>{row.total_responses} lượt đánh giá</span>
                        {row.average_percentage !== null && (
                          <>
                            <span>·</span>
                            <span className="font-medium text-ink-2">
                              Đạt {row.average_percentage}% điểm tối đa
                            </span>
                          </>
                        )}
                      </p>
                    </div>
                  </div>

                  {/* Right: Score, Progress Bar & Percentage */}
                  <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 pl-12 sm:pl-0">
                    {/* Visual Progress Bar (Hidden on ultra-small mobile screens) */}
                    <div className="hidden md:flex flex-col items-end w-36">
                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            percent >= 90
                              ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                              : percent >= 80
                              ? "bg-gradient-to-r from-indigo-500 to-blue-400"
                              : percent >= 70
                              ? "bg-gradient-to-r from-amber-500 to-yellow-400"
                              : "bg-gradient-to-r from-rose-500 to-orange-400"
                          }`}
                          style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
                        />
                      </div>
                    </div>

                    {/* Numeric Score */}
                    <div className="text-right">
                      <div className="flex items-baseline justify-end gap-1">
                        <span className="font-mono text-lg sm:text-xl font-bold tracking-tight text-ink">
                          {row.average_total_score}
                        </span>
                        {data.max_possible_score && (
                          <span className="font-mono text-xs text-muted">
                            /{data.max_possible_score}
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-muted">Điểm trung bình</span>
                    </div>

                    {/* Percentage Pill */}
                    {row.average_percentage !== null && (
                      <div className="w-16 text-right">
                        <span
                          className={`inline-flex items-center justify-center rounded-lg px-2.5 py-1 text-xs font-bold font-mono ${
                            percent >= 90
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : percent >= 80
                              ? "bg-indigo-50 text-indigo-700 border border-indigo-200"
                              : percent >= 70
                              ? "bg-amber-50 text-amber-800 border border-amber-200"
                              : "bg-rose-50 text-rose-700 border border-rose-200"
                          }`}
                        >
                          {row.average_percentage}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Trust & Transparency Guarantee Footer */}
      <footer className="mt-8 rounded-2xl border border-rule bg-paper p-5 sm:p-6 shadow-card">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 ring-4 ring-emerald-50/50">
              <IconShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-ink">Minh Bạch & Khách Quan Tuyệt Đối</p>
              <p className="text-xs text-muted">
                Dữ liệu xếp hạng được tổng hợp tự động từ kết quả khảo sát thực tế của người dân và tổ chức.
              </p>
            </div>
          </div>

          <Link
            to={`/khao-sat/${slug}`}
            className="btn btn-secondary text-xs inline-flex items-center gap-1.5 shrink-0"
          >
            <span>Đóng góp ý kiến của bạn</span>
            <IconArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </footer>
    </PublicShell>
  );
}

