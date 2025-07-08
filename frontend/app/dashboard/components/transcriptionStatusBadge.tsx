import { FC } from "react";
import { CheckCircle, Clock, AlertCircle } from "lucide-react";

interface TranscriptionStatusBadgeProps {
  status: string;
}

const TranscriptionStatusBadge: FC<TranscriptionStatusBadgeProps> = ({
  status,
}) => {
  switch (status) {
    case "completed":
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case "processing":
      return <Clock className="h-4 w-4 text-yellow-500" />;
    case "failed":
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Clock className="h-4 w-4 text-gray-500" />;
  }
};

export default TranscriptionStatusBadge;
