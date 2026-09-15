import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useSurveyBranchLimits, useSetSurveyBranchLimits } from "../../hooks/useSurveys";
import { apiErrorMessage } from "../../lib/api";
import { Button, Card, TextInput } from "../ui/primitives";
import { LoadingState, ErrorState } from "../ui/DataStates";

export function BranchLimitsCard({ surveyId, canEdit }) {
  const { data, isLoading, isError, error, refetch } = useSurveyBranchLimits(surveyId);
  const setLimits = useSetSurveyBranchLimits(surveyId);
  const [drafts, setDrafts] = useState({});

  useEffect(() => {
    if (data) {
      setDrafts(Object.fromEntries(data.map((r) => [r.branch_id, r.max_responses ?? ""])));
    }
  }, [data]);

  const onSave = async () => {
    const items = Object.entries(drafts).map(([branch_id, value]) => ({
      branch_id: Number(branch_id),
      max_responses: value === "" ? null : Number(value),
    }));
    try {
      await setLimits.mutateAsync(items);
      toast.success("Đã lưu chỉ tiêu theo chi nhánh");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  if (isLoading) return <Card><LoadingState /></Card>;
  if (isError) return <Card><ErrorState error={error} onRetry={refetch} /></Card>;
  if (!data?.length) return null;

  return (
    <Card>
      <h3 className="mb-1 font-semibold text-slate-800">Chỉ tiêu số lượt theo chi nhánh</h3>
      <p className="mb-3 text-xs text-muted">
        Để trống = không giới hạn. Khi một chi nhánh đủ số lượt, trang khảo sát công khai sẽ khoá,
        không nhận thêm phản hồi gán cho chi nhánh đó.
      </p>
      <div className="grid gap-2">
        {data.map((row) => (
          <div key={row.branch_id} className="flex items-center gap-3">
            <span className="flex-1 truncate text-sm text-ink">{row.branch_name}</span>
            <span className="text-xs text-muted">Đã nhận: {row.response_count}</span>
            <TextInput
              type="number"
              min="1"
              className="w-24"
              placeholder="Không giới hạn"
              value={drafts[row.branch_id] ?? ""}
              onChange={(e) => setDrafts((d) => ({ ...d, [row.branch_id]: e.target.value }))}
              disabled={!canEdit}
            />
          </div>
        ))}
      </div>
      {canEdit && (
        <div className="mt-3">
          <Button onClick={onSave} disabled={setLimits.isPending}>
            Lưu chỉ tiêu
          </Button>
        </div>
      )}
    </Card>
  );
}
