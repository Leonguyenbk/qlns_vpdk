import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { useEmployee, useEmployeeMutations } from "../../hooks/useEmployees";
import { EmployeeForm } from "../../components/employees/EmployeeForm";
import { PageHeader, Button } from "../../components/ui/primitives";
import { LoadingState, ErrorState } from "../../components/ui/DataStates";
import { apiErrorMessage } from "../../lib/api";

export default function EmployeeEditPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch } = useEmployee(id);
  const { update } = useEmployeeMutations();

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const defaults = {
    employee_code: data.employee_code,
    full_name: data.full_name,
    date_of_birth: data.date_of_birth || "",
    gender: data.gender || "",
    identity_number: data.identity_number || "",
    phone: data.phone || "",
    email: data.email || "",
    address: data.address || "",
    professional_title: data.professional_title || "",
    employment_type: data.employment_type || "",
    recruitment_date: data.recruitment_date || "",
    status: data.status,
    notes: data.notes || "",
  };

  const onSubmit = async (values) => {
    const body = { ...values };
    Object.keys(body).forEach((k) => body[k] === "" && (body[k] = null));
    try {
      await update.mutateAsync({ id, body });
      toast.success("Cập nhật nhân sự thành công");
      navigate(`/employees/${id}`);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title={`Chỉnh sửa: ${data.full_name}`}
        subtitle="Chỉnh sửa hồ sơ không thay đổi đơn vị/chức vụ. Dùng chức năng Chuyển đơn vị để điều chuyển."
        actions={<Button variant="secondary" onClick={() => navigate(-1)}>Quay lại</Button>}
      />
      <EmployeeForm
        mode="edit"
        defaultValues={defaults}
        submitting={update.isPending}
        onSubmit={onSubmit}
      />
    </div>
  );
}
