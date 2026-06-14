import { Navigate, RouterProvider, createBrowserRouter } from "react-router-dom";

import RequireAuth from "./components/auth/RequireAuth";
import AppLayout from "./layouts/AppLayout";
import Dashboard from "./pages/Dashboard";
import Diagnose from "./pages/Diagnose";
import DiagnosisDetail from "./pages/DiagnosisDetail";
import Login from "./pages/Login";
import Patients from "./pages/Patients";
import PatientDetail from "./pages/PatientDetail";
import Users from "./pages/Users";
import ErrorPage from "./pages/ErrorPage";

const router = createBrowserRouter([
  { path: "/login", element: <Login /> },
  {
    path: "/",
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <RequireAuth roles={["doctor"]}><Dashboard /></RequireAuth> },
      { path: "diagnose", element: <RequireAuth roles={["doctor"]}><Diagnose /></RequireAuth> },
      { path: "diagnose/:id", element: <DiagnosisDetail /> },
      { path: "patients", element: <RequireAuth roles={["doctor"]}><Patients /></RequireAuth> },
      { path: "patients/:id", element: <PatientDetail /> },
      { path: "users", element: <RequireAuth roles={["doctor"]}><Users /></RequireAuth> },
      { path: "my-records", element: <PatientDetail /> },
      { path: "404", element: <ErrorPage /> },
      { path: "*", element: <Navigate to="/404" replace /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
