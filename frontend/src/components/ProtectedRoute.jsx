import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-mm">
        <p className="font-serif-mm italic text-mm-secondary mm-pulse" data-testid="route-loader">
          Preparing your space...
        </p>
      </div>
    );
  }
  if (!user) return <Navigate to="/" replace />;
  return children;
}
