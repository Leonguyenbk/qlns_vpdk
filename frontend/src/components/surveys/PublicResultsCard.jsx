import toast from "react-hot-toast";
import { useSurveyMutations } from "../../hooks/useSurveys";
import { apiErrorMessage } from "../../lib/api";
import { Button, Card } from "../ui/primitives";

export function PublicResultsCard({ survey, canEdit }) {
  const { setResultsPublic } = useSurveyMutations();
  const publicUrl = `${window.location.origin}/ket-qua-khao-sat/${survey.slug}`;

  const onToggle = async (checked) => {
    try {
      await setResultsPublic.mutateAsync({ id: survey.id, is_results_public: checked });
      toast.success(checked ? "Đã công khai bảng xếp hạng" : "Đã ẩn bảng xếp hạng công khai");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(publicUrl);
      toast.success("Đã sao chép đường dẫn");
    } catch {
      toast.error("Không thể sao chép, vui lòng tự chọn và sao chép.");
    }
  };

  return (
    <Card>
      <h3 className="mb-1 font-semibold text-slate-800">Bảng xếp hạng công khai</h3>
      <p className="mb-3 text-xs text-muted">
        Công khai thứ hạng và điểm trung bình theo chi nhánh cho mọi người xem — không hiện chi
        tiết từng câu hỏi/câu trả lời. Bật được cả khi khảo sát đã đóng/lưu trữ.
      </p>
      <label className="flex items-center gap-2 text-sm text-ink">
        <input
          type="checkbox"
          checked={!!survey.is_results_public}
          disabled={!canEdit || setResultsPublic.isPending}
          onChange={(e) => onToggle(e.target.checked)}
        />
        Công khai bảng xếp hạng
      </label>
      {survey.is_results_public && (
        <div className="mt-3 flex items-center gap-2">
          <p className="min-w-0 flex-1 truncate rounded-lg border border-rule bg-canvas px-3 py-2 text-xs text-muted">
            {publicUrl}
          </p>
          <Button
            variant="secondary"
            className="shrink-0 px-2 py-1 text-xs"
            onClick={onCopy}
          >
            Sao chép
          </Button>
        </div>
      )}
    </Card>
  );
}
