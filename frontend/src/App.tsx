import { Navigate, RouterProvider, createBrowserRouter } from "react-router-dom";

import AppLayout from "./layouts/AppLayout";
import Dashboard from "./pages/Dashboard";
import Diagnose from "./pages/Diagnose";
import DiagnosisDetail from "./pages/DiagnosisDetail";
import Patients from "./pages/Patients";
import PatientDetail from "./pages/PatientDetail";
import ErrorPage from "./pages/ErrorPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "diagnose", element: <Diagnose /> },
      { path: "diagnose/:id", element: <DiagnosisDetail /> },
      { path: "patients", element: <Patients /> },
      { path: "patients/:id", element: <PatientDetail /> },
      { path: "404", element: <ErrorPage /> },
      { path: "*", element: <Navigate to="/404" replace /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
