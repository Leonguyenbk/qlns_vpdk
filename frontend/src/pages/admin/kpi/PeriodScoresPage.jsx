import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { usePeriodScores, useKpiAdminMutations } from "../../../hooks/useKpi";
import { useAssignablePeople } from "../../../hooks/useTasks";
import { apiErrorMessage } from "../../../lib/api";
import { KPI_SCORE_STATUS_LABELS, KPI_SCORE_STATUS_BADGE } from "../../../lib/constants";
import { PageHeader, Button, Select } from "../../../components/ui/primitives";
import { Table } from "../../../components/ui/Table";
import { LoadingState, ErrorState, EmptyState } from "../../../components/ui/DataStates";

export default function PeriodScoresPage() {
  const { periodId } = useParams();
  const navigate = useNavigate();
  const { data: scores, isLoading, isError, error, refetch } = usePeriodScores(periodId);
  const { data: candidates } = useAssignablePeople({});
  const m = useKpiAdminMutations();
  const [userId, setUserId] = useState("");

  const onCompute = () => {
    if (!userId) return;
    m.computeScore.mutateAsync({ periodId: Number(periodId), userId: Number(userId) })
      .then(() => toast.success("Đã tính điểm tạm tính"))
      .catch((err) => toast.error(apiErrorMessage(err)));
  };

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const columns = [
    { key: "user", header: "Viên chức", render: (s) => <Link className="link font-medium" to={`/kpi/${s.id}`}>{s.user_full_name || `#${s.user_id}`}</Link> },
    { key: "status", header: "Trạng thái", render: (s) => <span className={`badge ${KPI_SCORE_STATUS_BADGE[s.status] || "badge-neutral"}`}>{KPI_SCORE_STATUS_LABELS[s.status] || s.status}</span> },
    { key: "provisional", header: "Tạm tính", render: (s) => s.provisional_total ?? "—" },
    { key: "confirmed", header: "Xác nhận", render: (s) => s.confirmed_total ?? "—" },
    { key: "official", header: "Chính thức", render: (s) => s.official_rating || "—" },
  ];

  return (
    <div className="space-y-5">
      <PageHeader
        title={`Kết quả KPI kỳ #${periodId}`}
        subtitle="Tính điểm tạm tính cho từng người, sau đó theo dõi luồng tự đánh giá → phê duyệt trong trang chi tiết."
        actions={<Button variant="secondary" onClick={() => navigate(-1)}>Quay lại</Button>}
      />
      <div className="card flex flex-wrap items-end gap-2 p-4">
        <div className="w-72">
          <label className="label">Tính điểm tạm tính cho</label>
          <Select value={userId} onChange={(e) => setUserId(e.target.value)}>
            <option value="">— Chọn người —</option>
            {candidates?.map((c) => <option key={c.user_id} value={c.user_id}>{c.full_name} — {c.unit_name || "?"}</option>)}
          </Select>
        </div>
        <Button disabled={!userId || m.computeScore.isPending} onClick={onCompute}>Tính điểm tạm tính</Button>
      </div>
      <div className="card overflow-hidden">
        {scores.length === 0 ? <EmptyState title="Chưa có kết quả nào trong kỳ này" /> : <Table columns={columns} rows={scores} rowKey="id" />}
      </div>
    </div>
  );
}
