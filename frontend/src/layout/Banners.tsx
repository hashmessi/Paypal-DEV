import React, { useEffect, useState } from 'react'
import { Banner } from '../components/ui/Banner'
import { subscribeServerStatus, type ServerStatus } from '../lib/api'
import { getDemoClockOffsetMs, setDemoClockOffsetDays } from '../lib/time'
import { Button } from '../components/ui/Button'

export const Banners: React.FC = () => {
  const [serverState, setServerState] = useState<ServerStatus>({ isWakingUp: false })
  const [clockOffset, setClockOffset] = useState(getDemoClockOffsetMs())

  useEffect(() => {
    return subscribeServerStatus((status) => {
      setServerState(status)
    })
  }, [])

  const handleResetClock = () => {
    setDemoClockOffsetDays(0)
    setClockOffset(0)
    window.location.reload()
  }

  return (
    <div className="w-full flex flex-col">
      {serverState.isWakingUp && (
        <Banner
          tone="warn"
          title="Server notice:"
          body="Waking the sandbox server. This can take up to a minute on the free tier. Retrying automatically..."
        />
      )}

      {clockOffset > 0 && (
        <Banner
          tone="warn"
          title="Simulated clock active:"
          body="Time is currently advanced +30 days. Prior authorizations have passed their expiration_time."
          action={
            <Button size="sm" variant="secondary" onClick={handleResetClock}>
              Reset clock to real time
            </Button>
          }
        />
      )}
    </div>
  )
}
