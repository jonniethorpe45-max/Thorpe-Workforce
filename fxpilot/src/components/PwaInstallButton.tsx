import { Download } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { usePwaInstall } from '@/hooks/usePwaInstall'

export function PwaInstallButton() {
  const { canInstall, installed, install } = usePwaInstall()

  if (installed) {
    return (
      <Button size="lg" variant="outline" disabled>
        Installed
      </Button>
    )
  }

  if (!canInstall) {
    return null
  }

  return (
    <Button
      size="lg"
      variant="outline"
      onClick={() => {
        void install()
      }}
    >
      <Download className="mr-2 h-4 w-4" />
      Install App
    </Button>
  )
}
