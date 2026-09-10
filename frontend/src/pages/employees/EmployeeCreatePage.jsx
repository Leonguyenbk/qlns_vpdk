import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useEmployeeMutations } from "../../hooks/useEmployees";
import { EmployeeForm } from "../../components/employees/EmployeeForm";
import { PageHeader, Button } from "../../components/ui/primitives";
import { apiErrorMessage, conflictPayload } from "../../lib/api";
import { ConfirmDialog } from "../../components/ui/Modal";
import { useState } from "react";
import { todayISO } from "../../lib/format";

export default function EmployeeCreatePage() {
  const navigate = useNavigate();
  const { create } = useEmployeeMutations();
  const [conflict, setConflict] = useState(null);
  const [lastValues, setLastValues] = useState(null);

  const buildPayload = (values, replace = false) => {
    const body = { ...values };
    Object.keys(body).forEach((k) => (body[k] === "" || body[k] === undefined) && delete body[k]);
    if (replace) body.replace_existing = true;
    return body;
  };

  const submit = async (values, replace = false) => {
    try {
      const res = await create.mutateAsync(buildPayload(values, replace));
      toast.success("Thêm nhân sự thành công");
      navigate(`/employees/${res.data.data.id}`);
    } catch (err) {
      const p = conflictPayload(err);
      if (p?.conflict === "POSITION_LIMIT_REACHED") {
        setLastValues(values);
        setConflict(p);
        return;
      }
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="Thêm nhân sự"
        actions={<Button variant="secondary" onClick={() => navigate(-1)}>Quay lại</Button>}
      />
      <EmployeeForm
        mode="create"
        defaultValues={{ status: "WORKING", recruitment_date: todayISO() }}
        submitting={create.isPending}
        onSubmit={(v) => submit(v, false)}
      />

      <ConfirmDialog
        open={!!conflict}
        onClose={() => setConflict(null)}
        onConfirm={() => {
          setConflict(null);
          submit(lastValues, true);
        }}
        loading={create.isPending}
        variant="primary"
        title="Chức vụ đã đủ người"
        confirmText="Thay thế người đang giữ"
        message={
          conflict
            ? `Chức vụ "${conflict.position?.name}" tại đơn vị đã đạt giới hạn. Người đang giữ: ` +
              conflict.current_holders.map((h) => `${h.full_name} (${h.employee_code})`).join(", ") +
              ". Xác nhận kết thúc phân công của người cũ và bổ nhiệm người mới?"
            : ""
        }
      />
    </div>
  );
}
