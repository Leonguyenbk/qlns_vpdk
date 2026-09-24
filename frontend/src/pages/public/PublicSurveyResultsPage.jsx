import { useParams } from "react-router-dom";
import { usePublicSurveyResults } from "../../hooks/usePublicSurvey";
import { Spinner } from "../../components/ui/Spinner";
import { apiErrorMessage } from "../../lib/api";

const RANK_MEDAL = { 1: "🥇", 2: "🥈", 3: "🥉" };

function Shell({ title, children }) {
  return (
    <div className="min-h-screen bg-canvas px-4 py-8">
      <div className="mx-auto w-full max-w-2xl">
        <div className="mb-6 text-center">
          <p className="eyebrow mb-1">Bảng xếp hạng khảo sát</p>
          {title && (
            <h1 className="font-display text-lg font-semibold tracking-tight text-ink">{title}</h1>
          )}
        </div>
        <div className="card p-5 sm:p-6">{children}</div>
      </div>
    </div>
  );
}

export default function PublicSurveyResultsPage() {
  const { slug } = useParams();
  const { data, isLoading, isError, error } = usePublicSurveyResults(slug);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas">
        <Spinner label="Đang tải bảng xếp hạng…" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <Shell>
        <p className="text-center text-ink-2">
          {apiErrorMessage(error, "Không tìm thấy khảo sát.")}
        </p>
      </Shell>
    );
  }

  if (!data.available) {
    return (
      <Shell title={data.title}>
        <p className="text-center text-ink-2">
          {data.unavailable_reason || "Khảo sát này chưa công khai kết quả."}
        </p>
      </Shell>
    );
  }

  return (
    <Shell title={data.title}>
      <p className="mb-5 text-center text-sm text-muted">
        {data.total_responses} lượt đánh giá
        {data.max_possible_score ? ` · Thang điểm ${data.max_possible_score}` : ""}
      </p>

      {data.by_branch.length === 0 ? (
        <p className="text-center text-sm text-muted">Chưa có dữ liệu để xếp hạng.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {data.by_branch.map((row) => (
            <div
              key={row.branch_id}
              className="flex items-center gap-3 rounded-xl border border-rule px-4 py-3"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-canvas text-sm font-semibold text-ink-2">
                {RANK_MEDAL[row.rank] || row.rank || "—"}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-ink">{row.branch_name}</p>
                <p className="text-xs text-muted">{row.total_responses} lượt đánh giá</p>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-base font-semibold text-ink">{row.average_total_score}</p>
                {row.average_percentage !== null && (
                  <p className="text-xs text-muted">{row.average_percentage}%</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Shell>
  );
}
