import { useParams, useNavigate } from "react-router-dom";
import { useSurvey } from "../../hooks/useSurveys";
import { PageHeader, Button } from "../../components/ui/primitives";
import { SurveyResponsesView } from "../../components/surveys/SurveyResponsesView";

export default function SurveyResponsesPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: survey } = useSurvey(id);

  return (
    <div>
      <PageHeader
        title="Kết quả khảo sát"
        subtitle={survey?.title}
        actions={
          <Button variant="secondary" onClick={() => navigate(`/surveys/${id}`)}>
            ← Thông tin khảo sát
          </Button>
        }
      />
      <SurveyResponsesView surveyId={id} />
    </div>
  );
}
