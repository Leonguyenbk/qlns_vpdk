import { useNavigate, useParams } from "react-router-dom";
import { useEmployee, useEmployeeAssignments } from "../../hooks/useEmployees";
import { ASSIGNMENT_TYPE_LABELS } from "../../lib/constants";
import { formatDate } from "../../lib/format";
import { PageHeader, Button, Card, Badge } from "../../components/ui/primitives";
import { LoadingState, EmptyState, ErrorState } from "../../components/ui/DataStates";
import { Table } from "../../components/ui/Table";

export default function EmployeeHistoryPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: emp } = useEmployee(id, { includeDeleted: true });
  const { data, isLoading, isError, error, refetch } = useEmployeeAssignments(id);

  const columns = [
    { key: "unit_group", header: "Phòng / Chi nhánh", render: (r) => r.unit?.group_name || r.unit?.name },
    { key: "unit_section", header: "Bộ phận", render: (r) => r.unit?.section_name || "—" },
    { key: "position", header: "Chức vụ", render: (r) => r.position?.name },
    {
      key: "assignment_type",
      header: "Hình thức",
      render: (r) => ASSIGNMENT_TYPE_LABELS[r.assignment_type] || r.assignment_type,
    },
    { key: "start_date", header: "Từ ngày", render: (r) => formatDate(r.start_date) },
    {
      key: "end_date",
      header: "Đến ngày",
      render: (r) =>
        r.end_date ? (
          formatDate(r.end_date)
        ) : (
          <Badge className="bg-green-100 text-green-700">Đang hiệu lực</Badge>
        ),
    },
    { key: "decision_number", header: "Số QĐ", render: (r) => r.decision_number || "—" },
    { key: "note", header: "Ghi chú", render: (r) => r.note || "—" },
  ];

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="Lịch sử công tác & chuyển đơn vị"
        subtitle={emp ? `${emp.full_name} (${emp.employee_code})` : ""}
        actions={<Button variant="secondary" onClick={() => navigate(-1)}>Quay lại</Button>}
      />
      <Card className="overflow-hidden p-0">
        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : !data?.length ? (
          <EmptyState title="Chưa có dữ liệu công tác" />
        ) : (
          <Table columns={columns} rows={data} />
        )}
      </Card>
    </div>
  );
}
