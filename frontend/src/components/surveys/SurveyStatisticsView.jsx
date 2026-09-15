import { useState } from "react";
import { useSurveyStatistics } from "../../hooks/useSurveyResponses";
import { formatDate } from "../../lib/format";
import { Card } from "../ui/primitives";
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
          {stats.options.length ? (
            <div className="grid gap-2.5">
              {stats.options.map((o) => (
                <BarRow
                  key={o.option_id}
                  label={o.option_text}
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
        <div className="grid gap-2.5">
          <BarRow label="Có" percentage={stats.yes_percentage} valueLabel={`${stats.yes_count} · ${stats.yes_percentage}%`} color="var(--color-ok)" />
          <BarRow label="Không" percentage={stats.no_percentage} valueLabel={`${stats.no_count} · ${stats.no_percentage}%`} color="var(--color-danger)" />
        </div>
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
  const [filters, setFilters] = useState({ preset: "", date_from: "", date_to: "", branch_id: "" });
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
  const { data, isLoading, isError, error, refetch } = useSurveyStatistics(surveyId, params);

  const setFilter = (patch) => setFilters((f) => ({ ...f, ...patch }));

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;
  if (!data) return null;

  const { overview, by_question, time_series, by_branch } = data;
  const maxSeries = Math.max(1, ...time_series.map((t) => t.count));
  const maxBranch = Math.max(1, ...by_branch.map((b) => b.total_responses));

  return (
    <div>
      <SurveyFilterBar filters={filters} onChange={setFilter} />

      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-5">
        <KpiTile label="Tổng lượt khảo sát" value={overview.total_responses} />
        <KpiTile label="Tỷ lệ hoàn thành" value={`${overview.completion_rate}%`} />
        <KpiTile label="Điểm trung bình" value={overview.average_score != null ? `${overview.average_score}/5` : "—"} />
        <KpiTile label="Tỷ lệ hài lòng" value={`${overview.satisfaction_rate}%`} hint="Đánh giá 4–5 sao" />
        <KpiTile label="Tỷ lệ không hài lòng" value={`${overview.dissatisfaction_rate}%`} hint="Đánh giá 1–2 sao" />
      </div>

      {overview.total_responses > 0 && (
        <Card className="mb-6">
          <h3 className="mb-3 font-semibold text-slate-800">Phân bố mức độ hài lòng</h3>
          <RatingBreakdown breakdown={overview.rating_breakdown} />
        </Card>
      )}

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="mb-3 font-semibold text-slate-800">Lượt đánh giá theo ngày</h3>
          {time_series.length ? (
            <div className="grid max-h-72 gap-2.5 overflow-y-auto">
              {time_series.map((t) => (
                <BarRow
                  key={t.date}
                  label={formatDate(t.date)}
                  percentage={(t.count / maxSeries) * 100}
                  valueLabel={t.count}
                />
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted">Chưa có dữ liệu.</p>
          )}
        </Card>

        <Card>
          <h3 className="mb-3 font-semibold text-slate-800">Theo chi nhánh</h3>
          {by_branch.length ? (
            <div className="grid gap-3">
              {by_branch.map((b) => (
                <div key={b.branch_id ?? "none"}>
                  <BarRow
                    label={b.branch_name}
                    percentage={(b.total_responses / maxBranch) * 100}
                    valueLabel={`${b.total_responses} lượt`}
                  />
                  <p className="mt-1 text-xs text-muted">
                    Điểm TB {b.average_score ?? "—"}/5 · Hài lòng {b.satisfaction_rate}% · Không hài lòng{" "}
                    {b.dissatisfaction_rate}%
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
          {by_question.map((q) => (
            <QuestionStatCard key={q.id} question={q} />
          ))}
        </div>
      ) : (
        <EmptyState title="Khảo sát chưa có câu hỏi đang hoạt động" />
      )}
    </div>
  );
}
