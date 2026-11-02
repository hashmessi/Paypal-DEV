import { createBrowserRouter, Navigate } from 'react-router'
import { AppShell } from './layout/AppShell'
import { StartPage } from './pages/Start'
import { ShopPage } from './pages/Shop/ShopPage'
import { ReceiptsPage } from './pages/Receipts'
import { ReceiptPage } from './pages/Receipt'
import { ReplayPage } from './pages/Replay'
import { TowerPage } from './pages/Tower'
import { DriftReviewPage } from './pages/DriftReview'
import { EventsPage } from './pages/Events'
import { ProofPage } from './pages/Proof'
import { SpinePage } from './pages/Spine'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <StartPage />,
      },
      {
        path: 'shop',
        element: <ShopPage />,
      },
      {
        path: 'receipts',
        element: <ReceiptsPage />,
      },
      {
        path: 'receipts/:id',
        element: <ReceiptPage />,
      },
      {
        path: 'receipts/:id/replay',
        element: <ReplayPage />,
      },
      {
        path: 'tower',
        element: <TowerPage />,
      },
      {
        path: 'tower/cases/:id',
        element: <DriftReviewPage />,
      },
      {
        path: 'events',
        element: <EventsPage />,
      },
      {
        path: 'proof',
        element: <ProofPage />,
      },
      {
        path: 'spine',
        element: <SpinePage />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
])

