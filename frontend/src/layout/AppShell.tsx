import React, { useState } from 'react'
import { Outlet } from 'react-router'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { Banners } from './Banners'
import { useTower } from '../queries/useTower'

export const AppShell: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { data: towerData } = useTower()

  return (
    <div className="min-h-screen bg-[var(--color-canvas)] flex">
      {/* Sidebar */}
      <Sidebar
        driftCount={towerData?.openDriftCount || 0}
        isMobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main app area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar onToggleMobile={() => setMobileMenuOpen(!mobileMenuOpen)} />
        <Banners />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1280px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

