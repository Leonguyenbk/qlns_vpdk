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
    // Đơn vị / chức vụ của phân công chính (sửa tại chỗ)
    unit_id: data.current_unit?.id ?? "",
    position_id: data.current_position?.id ?? "",
    // Hồ sơ mở rộng
    place_of_origin: data.place_of_origin || "",
    identity_issued_date: data.identity_issued_date || "",
    identity_issued_place: data.identity_issued_place || "",
    job_grade_code: data.job_grade_code || "",
    job_duties: data.job_duties || "",
    tenure_date: data.tenure_date || "",
    contract_type: data.contract_type || "",
    education_level: data.education_level || "",
    education_major: data.education_major || "",
    education_mode: data.education_mode || "",
    foreign_language_cert: data.foreign_language_cert || "",
    it_cert: data.it_cert || "",
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
        subtitle="Sửa được cả chức vụ và đơn vị của phân công hiện tại. Điều chuyển kèm quyết định thì dùng chức năng Chuyển đơn vị."
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
