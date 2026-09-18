import { useState } from "react";
import toast from "react-hot-toast";
import { useSurveyStatistics } from "../../hooks/useSurveyResponses";
import { exportSurveySummary } from "../../hooks/useSurveys";
import { useCan } from "../Can";
import { PERMISSIONS } from "../../lib/constants";
import { apiErrorMessage } from "../../lib/api";
import { Button, Card } from "../ui/primitives";
import { LoadingState, ErrorState, EmptyState } from "../ui/DataStates";
import { SurveyFilterBar } from "./SurveyFilterBar";
import { KpiTile } from "./charts/KpiTile";
import { RatingBreakdown } from "./charts/RatingBreakdown";
import { BarRow } from "./charts/BarRow";

function QuestionStatCard({ question }) {
  const { stats } = question;
  return (
    <Card>
      <p className="mb-3 text-sm font-medium text-ink">{question.question_text}</p>
      {stats.type === "choice" && (
        <>
          {stats.average_score != null && (
            <p className="mb-3 text-sm text-ink-2">
              Điểm trung bình: <span className="font-semibold text-ink">{stats.average_score}</span>
              <span className="ml-1 text-xs text-muted">({stats.scored_answers} đáp án có điểm)</span>
            </p>
          )}
          {stats.options.length ? (
            <div className="grid gap-2.5">
              {stats.options.map((o) => (
                <BarRow
                  key={o.option_id}
                  label={`${o.option_text}${o.score != null ? ` · ${o.score} điểm` : ""}`}
                  percentage={o.percentage}
                  valueLabel={`${o.count} · ${o.percentage}%`}
                />
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted">Chưa có phản hồi.</p>
          )}
        </>
      )}
      {stats.type === "yes_no" && (
        <>
          {stats.average_score != null && (
            <p className="mb-3 text-sm text-ink-2">
              Điểm trung bình: <span className="font-semibold text-ink">{stats.average_score}</span>
            </p>
          )}
          <div className="grid gap-2.5">
            <BarRow label={`Có${stats.yes_score != null ? ` · ${stats.yes_score} điểm` : ""}`} percentage={stats.yes_percentage} valueLabel={`${stats.yes_count} · ${stats.yes_percentage}%`} color="var(--color-ok)" />
            <BarRow label={`Không${stats.no_score != null ? ` · ${stats.no_score} điểm` : ""}`} percentage={stats.no_percentage} valueLabel={`${stats.no_count} · ${stats.no_percentage}%`} color="var(--color-danger)" />
          </div>
        </>
      )}
      {stats.type === "rating" && (
        <>
          {stats.average != null && (
            <p className="mb-2 text-sm text-ink-2">
              Điểm trung bình: <span className="font-semibold text-ink">{stats.average}/5</span>
            </p>
          )}
          <RatingBreakdown breakdown={stats.breakdown} />
        </>
      )}
      {stats.type === "number" && (
        <div className="flex gap-6 text-sm text-ink-2">
          <span>
            Trung bình: <span className="font-semibold text-ink">{stats.average ?? "—"}</span>
          </span>
          <span>
            Nhỏ nhất: <span className="font-semibold text-ink">{stats.min ?? "—"}</span>
          </span>
          <span>
            Lớn nhất: <span className="font-semibold text-ink">{stats.max ?? "—"}</span>
          </span>
        </div>
      )}
      {stats.type === "open_text" && (
        <>
          {stats.samples.length ? (
            <ul className="grid max-h-56 gap-2 overflow-y-auto text-sm text-ink-2">
              {stats.samples.map((s, i) => (
                <li key={i} className="rounded-lg bg-paper-2 px-3 py-2">
                  {s}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">Chưa có ý kiến nào.</p>
          )}
        </>
      )}
    </Card>
  );
}

export function SurveyStatisticsView({ surveyId }) {
  const [filters, setFilters] = useState({ branch_id: "" });
  const [exporting, setExporting] = useState(false);
  const { can } = useCan();
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
  const { data, isLoading, isError, error, refetch } = useSurveyStatistics(surveyId, params);

  const setFilter = (patch) => setFilters((f) => ({ ...f, ...patch }));

  const onExport = async () => {
    setExporting(true);
    try {
      await exportSurveySummary(surveyId, params);
    } catch (err) {
      toast.error(apiErrorMessage(err, "Xuất Excel thất bại"));
    } finally {
      setExporting(false);
    }
  };

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;
  if (!data) return null;

  const { overview, by_question, by_branch } = data;
  const topBranches = by_branch.filter((b) => b.rank === 1);
  const branchScores = by_branch.map((b) => b.average_score).filter((score) => score != null);
  const minBranchScore = branchScores.length ? Math.min(...branchScores) : 0;
  const maxBranchScore = branchScores.length ? Math.max(...branchScores) : 0;
  const branchScoreWidth = (score) => {
    if (score == null) return 0;
    if (maxBranchScore === minBranchScore) return 100;
    return ((score - minBranchScore) / (maxBranchScore - minBranchScore)) * 100;
  };

  return (
    <div>
      <div className="mb-1 flex items-start justify-between gap-3">
        <SurveyFilterBar filters={filters} onChange={setFilter} branchOnly />
        {can(PERMISSIONS.SURVEY_EXPORT) && (
          <Button variant="secondary" onClick={onExport} disabled={exporting}>
            {exporting ? "Đang xuất…" : "Xuất Excel"}
          </Button>
        )}
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-3">
        <KpiTile label="Tổng lượt khảo sát" value={overview.total_responses} />
        <KpiTile label="Tỷ lệ hoàn thành" value={`${overview.completion_rate}%`} />
        <KpiTile
          label="Điểm trung bình"
          value={overview.average_score != null ? overview.average_score : "—"}
          hint={`${overview.score_answer_count || 0} đáp án có gán điểm`}
        />
      </div>

      <div className="mb-6">
        <Card>
          <h3 className="mb-3 font-semibold text-slate-800">Xếp hạng điểm theo chi nhánh</h3>
          {by_branch.length ? (
            <div className="grid gap-3">
              {topBranches.length > 0 && (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                    {topBranches.length > 1 ? "Các chi nhánh đồng dẫn đầu" : "Chi nhánh dẫn đầu"}
                  </p>
                  <p className="mt-1 font-semibold text-emerald-950">
                    {topBranches.map((b) => b.branch_name).join(", ")}
                  </p>
                  <p className="text-sm text-emerald-800">
                    {topBranches[0].average_score} điểm
                  </p>
                </div>
              )}
              {by_branch.map((b) => (
                <div key={b.branch_id ?? "none"}>
                  <BarRow
                    label={`${b.rank ? `#${b.rank} · ` : ""}${b.branch_name}`}
                    percentage={branchScoreWidth(b.average_score)}
                    valueLabel={b.average_score != null ? `${b.average_score} điểm` : "Chưa có điểm"}
                  />
                  <p className="mt-1 text-xs text-muted">
                    {b.total_responses} lượt · {b.scored_answers || 0} đáp án có điểm
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted">Chưa có dữ liệu.</p>
          )}
        </Card>
      </div>

      <h3 className="mb-3 font-display text-base font-semibold text-ink">Thống kê theo câu hỏi</h3>
      {by_question.length ? (
        <div className="grid gap-4">
          {by_question.map((q, i) => {
            const showSectionHeader = q.section && q.section !== by_question[i - 1]?.section;
            return (
              <div key={q.id}>
                {showSectionHeader && (
                  <h4 className="mb-2 mt-2 font-display text-sm font-semibold text-ink first:mt-0">
                    {q.section}
                  </h4>
                )}
                <QuestionStatCard question={q} />
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState title="Khảo sát chưa có câu hỏi đang hoạt động" />
      )}
    </div>
  );
}
