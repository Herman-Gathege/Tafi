import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { AppShell } from "@/components/app-shell";
import { PublicShell } from "@/components/public-shell";
import { RequireAuth, RequirePlatformAdmin } from "@/components/require-auth";
import { AcceptInvitePage } from "@/routes/accept-invite";
import { AdminPage } from "@/routes/admin";
import { DashboardPage } from "@/routes/dashboard";
import { ForgotPasswordPage } from "@/routes/forgot-password";
import { LandingPage } from "@/routes/landing";
import { ResetPasswordPage } from "@/routes/reset-password";
import { SignInPage } from "@/routes/signin";
import { WireframesPage } from "@/routes/wireframes";

const router = createBrowserRouter([
  {
    path: "/",
    element: <PublicShell />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: "wireframes", element: <WireframesPage /> },
      { path: "signin", element: <SignInPage /> },
      { path: "accept-invite", element: <AcceptInvitePage /> },
      { path: "forgot-password", element: <ForgotPasswordPage /> },
      { path: "reset-password", element: <ResetPasswordPage /> },
    ],
  },
  {
    path: "/app",
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <DashboardPage /> },
          {
            path: "admin",
            element: <RequirePlatformAdmin />,
            children: [{ index: true, element: <AdminPage /> }],
          },
        ],
      },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
