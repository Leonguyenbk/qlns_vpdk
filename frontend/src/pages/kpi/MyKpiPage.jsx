import { Link } from "react-router-dom";
import { useMyScores } from "../../hooks/useKpi";
import { PageHeader } from "../../components/ui/primitives";
import { LoadingState, ErrorState, EmptyState } from "../../components/ui/DataStates";
import { Table } from "../../components/ui/Table";
import { KPI_SCORE_STATUS_LABELS, KPI_SCORE_STATUS_BADGE } from "../../lib/constants";

export default function MyKpiPage() {
  const { data, isLoading, isError, error, refetch } = useMyScores();

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const columns = [
    { key: "period", header: "Kỳ", render: (s) => <Link className="link font-medium" to={`/kpi/${s.id}`}>#{s.id} — Kỳ {s.period_id}</Link> },
    { key: "status", header: "Trạng thái", render: (s) => (
        <span className={`badge ${KPI_SCORE_STATUS_BADGE[s.status] || "badge-neutral"}`}>
          {KPI_SCORE_STATUS_LABELS[s.status] || s.status}
        </span>
      ) },
    { key: "provisional", header: "Điểm tạm tính", render: (s) => s.provisional_total ?? "—" },
    { key: "self", header: "Tự đánh giá", render: (s) => s.self_assessed_total ?? "—" },
    { key: "confirmed", header: "Điểm xác nhận", render: (s) => s.confirmed_total ?? "—" },
    { key: "proposed", header: "Mức đề xuất", render: (s) => s.proposed_rating || "—" },
    { key: "official", header: "Kết quả chính thức", render: (s) => s.official_rating || "Chưa có" },
  ];

  return (
    <div>
      <PageHeader
        title="KPI của tôi"
        subtitle="Toàn bộ dự thảo/thí điểm theo Nghị định số 233/2026/NĐ-CP — chưa phải kết quả chính thức cho đến khi được phê duyệt."
      />
      <div className="card overflow-hidden">
        {data.length === 0 ? (
          <EmptyState title="Chưa có kết quả KPI nào" description="Bộ phận tổ chức cán bộ sẽ tính điểm khi kỳ đánh giá được mở." />
        ) : (
          <Table columns={columns} rows={data} rowKey="id" />
        )}
      </div>
    </div>
  );
}
