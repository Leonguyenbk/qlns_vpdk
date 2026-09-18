import { useParams } from "react-router-dom";
import { SurveyResponsesView } from "../../components/surveys/SurveyResponsesView";

export default function SurveyResponsesPage() {
  const { id } = useParams();
  return <SurveyResponsesView surveyId={id} />;
}
