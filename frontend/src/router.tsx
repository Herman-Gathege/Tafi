import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { AppShell } from "@/components/app-shell";
import { PublicShell } from "@/components/public-shell";
import { RequireAuth } from "@/components/require-auth";
import { DashboardPage } from "@/routes/dashboard";
import { LandingPage } from "@/routes/landing";
import { OrganizationsPage } from "@/routes/organizations";
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
          { path: "organizations", element: <OrganizationsPage /> },
        ],
      },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
