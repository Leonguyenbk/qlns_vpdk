import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useSurveys, useSurveyMutations } from "../../hooks/useSurveys";
import { useCan } from "../../components/Can";
import {
  PERMISSIONS,
  SURVEY_STATUS_LABELS,
  SURVEY_STATUS_BADGE,
} from "../../lib/constants";
import { apiErrorMessage } from "../../lib/api";
import { formatDate, formatDateTimeSeconds } from "../../lib/format";
import {
  PageHeader,
  Button,
  Badge,
  TextInput,
  Select,
} from "../../components/ui/primitives";
import { Table, Pagination } from "../../components/ui/Table";
import {
  LoadingState,
  EmptyState,
  ErrorState,
} from "../../components/ui/DataStates";
import { ConfirmDialog } from "../../components/ui/Modal";
import { QRCodeModal } from "../../components/surveys/QRCodeModal";

const DEFAULT_FILTERS = { keyword: "", status: "", page: 1, page_size: 10 };

const NEXT_STATUS = {
  draft: { status: "active", label: "Xuất bản" },
  paused: { status: "active", label: "Mở lại" },
  closed: { status: "archived", label: "Lưu trữ" },
};
const PAUSE_STATUS = { status: "paused", label: "Tạm khóa" };
const CLOSE_STATUS = { status: "closed", label: "Đóng khảo sát" };

export default function SurveyListPage() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [qrSurvey, setQrSurvey] = useState(null);
  const navigate = useNavigate();
  const { can } = useCan();

  const params = useMemo(() => {
    const p = { ...filters };
    Object.keys(p).forEach((k) => p[k] === "" && delete p[k]);
    return p;
  }, [filters]);

  const { data, isLoading, isError, error, refetch } = useSurveys(params);
  const { remove, changeStatus, duplicate } = useSurveyMutations();

  const setFilter = (patch) => setFilters((f) => ({ ...f, ...patch, page: 1 }));

  const onDelete = async () => {
    try {
      await remove.mutateAsync(pendingDelete.id);
      toast.success("Đã xóa khảo sát");
      setPendingDelete(null);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onChangeStatus = async (survey, status, label) => {
    try {
      await changeStatus.mutateAsync({ id: survey.id, status });
      toast.success(`${label} thành công`);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onDuplicate = async (survey) => {
    try {
      const resp = await duplicate.mutateAsync(survey.id);
      toast.success("Đã sao chép khảo sát");
      navigate(`/surveys/${resp.data.data.id}`);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const columns = [
    {
      key: "title",
      header: "Tên khảo sát",
      render: (r) => (
        <Link
          to={`/surveys/${r.id}`}
          className="font-medium text-brand-700 hover:underline"
        >
          {r.title}
        </Link>
      ),
    },
    {
      key: "status",
      header: "Trạng thái",
      render: (r) => (
        <Badge className={SURVEY_STATUS_BADGE[r.status]}>
          {SURVEY_STATUS_LABELS[r.status]}
        </Badge>
      ),
    },
    {
      key: "question_count",
      header: "Số câu hỏi",
      render: (r) => r.question_count ?? 0,
    },
    {
      key: "response_count",
      header: "Lượt phản hồi",
      render: (r) => r.response_count ?? 0,
    },
    {
      key: "start_at",
      header: "Bắt đầu",
      render: (r) => formatDateTimeSeconds(r.start_at),
    },
    { key: "end_at", header: "Kết thúc", render: (r) => formatDateTimeSeconds(r.end_at) },
    {
      key: "created_by_name",
      header: "Người tạo",
      render: (r) => r.created_by_name || "—",
    },
    {
      key: "created_at",
      header: "Ngày tạo",
      render: (r) => formatDate(r.created_at),
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (r) => {
        const next = NEXT_STATUS[r.status];
        return (
          <div className="flex flex-wrap justify-end gap-1">
            <Button
              variant="ghost"
              className="px-2 py-1 text-xs"
              onClick={() => navigate(`/surveys/${r.id}/questions`)}
            >
              Câu hỏi
            </Button>
            {can(PERMISSIONS.SURVEY_VIEW_STATISTICS) && (
              <Button
                variant="ghost"
                className="px-2 py-1 text-xs"
                onClick={() => navigate(`/surveys/${r.id}/statistics`)}
              >
                Thống kê
              </Button>
            )}
            {r.status === "active" && (
              <Button
                variant="ghost"
                className="px-2 py-1 text-xs"
                onClick={() => setQrSurvey(r)}
              >
                QR
              </Button>
            )}
            {can(PERMISSIONS.SURVEY_UPDATE) && next && (
              <Button
                variant="ghost"
                className="px-2 py-1 text-xs text-emerald-700"
                onClick={() => onChangeStatus(r, next.status, next.label)}
              >
                {next.label}
              </Button>
            )}
            {can(PERMISSIONS.SURVEY_UPDATE) && r.status === "active" && (
              <Button
                variant="ghost"
                className="px-2 py-1 text-xs"
                onClick={() =>
                  onChangeStatus(r, PAUSE_STATUS.status, PAUSE_STATUS.label)
                }
              >
                {PAUSE_STATUS.label}
              </Button>
            )}
            {can(PERMISSIONS.SURVEY_UPDATE) &&
              (r.status === "active" || r.status === "paused") && (
                <Button
                  variant="ghost"
                  className="px-2 py-1 text-xs text-red-600"
                  onClick={() =>
                    onChangeStatus(r, CLOSE_STATUS.status, CLOSE_STATUS.label)
                  }
                >
                  {CLOSE_STATUS.label}
                </Button>
              )}
            {can(PERMISSIONS.SURVEY_CREATE) && (
              <Button
                variant="ghost"
                className="px-2 py-1 text-xs"
                onClick={() => onDuplicate(r)}
              >
                Sao chép
              </Button>
            )}
            {can(PERMISSIONS.SURVEY_DELETE) &&
              (!r.response_count || r.status === "archived") && (
              <Button
                variant="ghost"
                className="px-2 py-1 text-xs text-red-600"
                onClick={() => setPendingDelete(r)}
              >
                Xóa
              </Button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <div>
      <PageHeader
        title="Khảo sát – Đánh giá mức độ hài lòng"
        subtitle="Quản lý các cuộc khảo sát, câu hỏi và kết quả đánh giá của người dân"
      />

      {/* ── Thanh điều hướng nhanh ── */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {can(PERMISSIONS.SURVEY_CREATE) && (
          <Button onClick={() => navigate("/surveys/new")}>
            + Tạo khảo sát
          </Button>
        )}
        {can(PERMISSIONS.SURVEY_VIEW_STATISTICS) && (
          <Button
            variant="outline"
            onClick={() => navigate("/surveys/results")}
          >
            📋 Kết quả khảo sát
          </Button>
        )}
        {can(PERMISSIONS.SURVEY_VIEW_STATISTICS) && (
          <Button
            variant="outline"
            onClick={() => navigate("/surveys/statistics")}
          >
            📊 Thống kê
          </Button>
        )}
      </div>

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="min-w-[220px] flex-1">
          <TextInput
            placeholder="Tìm theo tên khảo sát…"
            value={filters.keyword}
            onChange={(e) => setFilter({ keyword: e.target.value })}
          />
        </div>
        <Select
          value={filters.status}
          onChange={(e) => setFilter({ status: e.target.value })}
          className="w-48"
        >
          <option value="">Tất cả trạng thái</option>
          {Object.entries(SURVEY_STATUS_LABELS).map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </Select>
      </div>

      <div className="card overflow-hidden p-0">
        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : (
          <>
            <Table
              columns={columns}
              rows={data?.items}
              empty={
                <EmptyState
                  title="Chưa có cuộc khảo sát nào"
                  action={
                    can(PERMISSIONS.SURVEY_CREATE) && (
                      <Button onClick={() => navigate("/surveys/new")}>
                        + Tạo khảo sát
                      </Button>
                    )
                  }
                />
              }
            />
            <Pagination
              pagination={data?.pagination}
              onChange={(page) => setFilters((f) => ({ ...f, page }))}
            />
          </>
        )}
      </div>

      <ConfirmDialog
        open={!!pendingDelete}
        onClose={() => setPendingDelete(null)}
        onConfirm={onDelete}
        loading={remove.isPending}
        title="Xóa khảo sát"
        message={
          pendingDelete?.response_count
            ? `Xóa vĩnh viễn khảo sát đã lưu trữ "${pendingDelete?.title}" cùng toàn bộ ${pendingDelete.response_count} phản hồi đã ghi nhận? Thao tác này không thể hoàn tác.`
            : `Xóa vĩnh viễn khảo sát "${pendingDelete?.title}"? Thao tác này không thể hoàn tác.`
        }
        confirmText="Xóa"
      />

      <QRCodeModal survey={qrSurvey} onClose={() => setQrSurvey(null)} />
    </div>
  );
}
