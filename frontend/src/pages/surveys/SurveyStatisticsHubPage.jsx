import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSurveys } from "../../hooks/useSurveys";
import { Select } from "../../components/ui/primitives";
import { EmptyState, LoadingState } from "../../components/ui/DataStates";
import { SurveyStatisticsView } from "../../components/surveys/SurveyStatisticsView";

export default function SurveyStatisticsHubPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useSurveys({ page_size: 100 });
  const [surveyId, setSurveyId] = useState("");
  const surveys = data?.items || [];

  // Mặc định chọn cuộc khảo sát đang diễn ra mới nhất (danh sách đã sắp mới nhất
  // trước); chỉ tự chọn một lần lúc vào trang, không ghi đè lựa chọn của người dùng.
  const autoSelected = useRef(false);
  useEffect(() => {
    if (autoSelected.current || !data?.items?.length) return;
    autoSelected.current = true;
    const latestActive = data.items.find((s) => s.status === "active");
    if (latestActive) setSurveyId(String(latestActive.id));
  }, [data]);

  return (
    <div>
      <button
        type="button"
        onClick={() => navigate("/surveys")}
        className="mb-4 flex items-center gap-1.5 text-sm text-muted hover:text-accent-text transition-colors"
      >
        ← Quay lại Danh sách khảo sát
      </button>
      {isLoading ? (
        <LoadingState />
      ) : !surveys.length ? (
        <EmptyState title="Chưa có cuộc khảo sát nào" />
      ) : (
        <>
          <div className="mb-5">
            <Select
              value={surveyId}
              onChange={(e) => setSurveyId(e.target.value)}
              className="w-full max-w-sm"
            >
              <option value="">-- Chọn cuộc khảo sát --</option>
              {surveys.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title}
                </option>
              ))}
            </Select>
          </div>
          {surveyId ? (
            <SurveyStatisticsView surveyId={surveyId} />
          ) : (
            <EmptyState title="Hãy chọn một cuộc khảo sát ở trên để xem thống kê" />
          )}
        </>
      )}
    </div>
  );
}
