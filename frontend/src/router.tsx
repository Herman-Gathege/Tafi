import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { AppShell } from "@/components/app-shell";
import { CrewShell } from "@/components/crew-shell";
import { PublicShell } from "@/components/public-shell";
import {
  RequireAuth,
  RequireCrew,
  RequirePlatformAdmin,
  RequireSchoolAdmin,
} from "@/components/require-auth";
import { AcceptInvitePage } from "@/routes/accept-invite";
import { AdminPage } from "@/routes/admin";
import { DashboardPage } from "@/routes/dashboard";
import { ForgotPasswordPage } from "@/routes/forgot-password";
import { GuardianInvitePage } from "@/routes/guardian-invite";
import { LandingPage } from "@/routes/landing";
import { ResetPasswordPage } from "@/routes/reset-password";
import { CrewTodayPage } from "@/routes/crew";
import { CrewTripPage } from "@/routes/crew/trip";
import { ChildrenPage } from "@/routes/school/children";
import { StopRequestsPage } from "@/routes/school/requests";
import { RoutesPage } from "@/routes/school/routes";
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
      // A guardian's link from WhatsApp: public, the token is the only key (S3-05).
      { path: "guardian-invite", element: <GuardianInvitePage /> },
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
            element: <RequireSchoolAdmin />,
            children: [
              { path: "children", element: <ChildrenPage /> },
              { path: "routes", element: <RoutesPage /> },
              { path: "requests", element: <StopRequestsPage /> },
            ],
          },
          {
            path: "admin",
            element: <RequirePlatformAdmin />,
            children: [{ index: true, element: <AdminPage /> }],
          },
        ],
      },
    ],
  },
  {
    path: "/crew",
    element: <RequireAuth />,
    children: [
      {
        element: <RequireCrew />,
        children: [
          {
            element: <CrewShell />,
            children: [
              { index: true, element: <CrewTodayPage /> },
              { path: "trips/:tripId", element: <CrewTripPage /> },
            ],
          },
        ],
      },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
