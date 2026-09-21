import { useState } from "react";
import toast from "react-hot-toast";
import { useSurveyResponses } from "../../hooks/useSurveyResponses";
import { exportSurvey } from "../../hooks/useSurveys";
import { useCan } from "../Can";
import { PERMISSIONS } from "../../lib/constants";
import { apiErrorMessage } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import { Button, Card } from "../ui/primitives";
import { Pagination } from "../ui/Table";
import { LoadingState, ErrorState, EmptyState } from "../ui/DataStates";
import { SurveyFilterBar } from "./SurveyFilterBar";

function ResponseCard({ response }) {
  const [open, setOpen] = useState(false);
  const contact = [response.respondent_phone, response.respondent_id_number, response.respondent_address]
    .filter(Boolean)
    .join(" · ");
  return (
    <Card className="p-4">
      <button type="button" className="flex w-full items-center justify-between gap-3 text-left" onClick={() => setOpen((o) => !o)}>
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink">{formatDateTime(response.submitted_at)}</p>
          <p className="truncate text-xs text-muted">
            {response.branch_name || "Không rõ chi nhánh"}
            {response.employee_name ? ` · ${response.employee_name}` : ""}
            {response.respondent_name ? ` · ${response.respondent_name}` : ""}
          </p>
        </div>
        <span className="shrink-0 text-xs text-muted">{open ? "Thu gọn ▲" : `${response.answers.length} câu trả lời ▼`}</span>
      </button>
      {open && (
        <div className="mt-3 grid gap-2 border-t border-rule pt-3">
          {contact && <p className="text-xs text-muted">{contact}</p>}
          {response.answers.map((a) => (
            <div key={a.id} className="text-sm">
              <p className="text-ink-2">
                {a.option_text && a.answer_text
                  ? `${a.option_text}: ${a.answer_text}`
                  : a.answer_text === "__none__"
                    ? "Không chọn phương án nào"
                    : a.answer_text ?? a.option_text ?? a.answer_number ?? "—"}
              </p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export function SurveyResponsesView({ surveyId }) {
  const [filters, setFilters] = useState({ preset: "", date_from: "", date_to: "", branch_id: "", page: 1 });
  const { can } = useCan();
  const [exporting, setExporting] = useState(false);
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
  const { data, isLoading, isError, error, refetch } = useSurveyResponses(surveyId, params);

  const setFilter = (patch) => setFilters((f) => ({ ...f, ...patch, page: 1 }));
  const setPage = (page) => setFilters((f) => ({ ...f, page }));

  const onExport = async () => {
    setExporting(true);
    try {
      const { page, ...rest } = params; // eslint-disable-line no-unused-vars
      await exportSurvey(surveyId, rest);
    } catch (err) {
      toast.error(apiErrorMessage(err, "Xuất Excel thất bại"));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      <div className="mb-1 flex items-start justify-between gap-3">
        <SurveyFilterBar filters={filters} onChange={setFilter} />
        {can(PERMISSIONS.SURVEY_EXPORT) && (
          <Button variant="secondary" onClick={onExport} disabled={exporting}>
            {exporting ? "Đang xuất…" : "Xuất Excel"}
          </Button>
        )}
      </div>

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : !data?.items?.length ? (
        <EmptyState title="Chưa có lượt phản hồi nào" />
      ) : (
        <>
          <div className="grid gap-3">
            {data.items.map((r) => (
              <ResponseCard key={r.id} response={r} />
            ))}
          </div>
          <div className="card mt-3 p-0">
            <Pagination pagination={data.pagination} onChange={setPage} />
          </div>
        </>
      )}
    </div>
  );
}
